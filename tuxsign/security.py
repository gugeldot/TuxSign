"""Hardening de proceso y utilidades de entrada segura.

Controles (ver SECURITY.md):
  * ISO 27002 A.8.12 / A.8.24: sin core dumps, ptrace ni lectura de memoria ajena.
  * ISO 27002 A.8.20 / A.8.22: la aplicación NO necesita red: Landlock (TCP) + seccomp (AF_INET/INET6/PACKET).
  * ISO 27002 A.8.9: seccomp deniega syscalls peligrosas (mount, bpf, kexec, módulos, keyctl…).
  * ISO 27002 A.8.26 / A.8.28: validación estricta de ficheros de entrada.
  * ISO 27002 A.8.5: limitación de intentos de autenticación (contraseña P12).
"""
from __future__ import annotations

import ctypes
import os
import platform
import resource
import stat
import struct
import sys
import time

MAX_PDF_BYTES = 200 * 1024 * 1024  # 200 MiB
MAX_P12_BYTES = 1 * 1024 * 1024  # 1 MiB
MAX_PDF_PAGES = 2000

_PR_SET_DUMPABLE = 4
_PR_SET_NO_NEW_PRIVS = 38
_SYS_LANDLOCK_CREATE_RULESET = 444
_SYS_LANDLOCK_RESTRICT_SELF = 446
_LANDLOCK_CREATE_RULESET_VERSION = 1 << 0
_LANDLOCK_ACCESS_NET_BIND_TCP = 1 << 0
_LANDLOCK_ACCESS_NET_CONNECT_TCP = 1 << 1


class InputRejected(ValueError):
    """Entrada rechazada. `key` es una clave i18n y la UI la traduce, así que aquí no hay texto fijo."""

    def __init__(self, key: str, **kw):
        super().__init__(key)
        self.key = key
        self.kw = kw


# --------------------------------------------------------------------------- proceso
def _trusted_sys_path() -> list[str]:
    """Rutas de import legítimas: bajo los prefijos del intérprete (o /app en Flatpak), no escribibles por otros."""
    roots = {os.path.realpath(x) for x in (sys.prefix, sys.base_prefix, sys.exec_prefix, "/usr", "/app")}
    out: list[str] = []
    for p in sys.path:
        if not p or not os.path.isdir(p):
            continue
        rp = os.path.realpath(p)
        if not any(rp == r or rp.startswith(r + os.sep) for r in roots):
            continue  # p. ej. PYTHONPATH=/tmp/evil o el directorio actual
        if os.stat(rp).st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            continue
        out.append(rp)
    return out


_ENV_DROP_PREFIX = ("PYTHON", "LD_", "QML", "GCONV", "GIO_", "NSS_", "MALLOC_")
_ENV_DROP = {"QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH", "QT_QPA_PLATFORMTHEME", "LOCPATH", "NLSPATH", "HOSTALIASES", "RES_OPTIONS"}
_ENV_KEEP_IN_FLATPAK = {"LD_LIBRARY_PATH", "QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH", "QML2_IMPORT_PATH", "QML_IMPORT_PATH"}


def clean_env(env: dict[str, str] | None = None) -> dict[str, str]:
    """Elimina variables que permiten inyectar código en el proceso (LD_PRELOAD, QT_PLUGIN_PATH, PYTHON*…).

    En Flatpak el propio runtime fija algunas rutas legítimas (LD_LIBRARY_PATH de GL, plugins de Qt): se conservan,
    porque el entorno del sandbox lo controla Flatpak y no el usuario.
    """
    env = dict(os.environ if env is None else env)
    sandbox = os.path.exists("/.flatpak-info")
    out: dict[str, str] = {}
    for k, v in env.items():
        if sandbox and k in _ENV_KEEP_IN_FLATPAK:
            out[k] = v
        elif k in _ENV_DROP or k.startswith(_ENV_DROP_PREFIX):
            continue
        else:
            out[k] = v
    return out


def interpreter_paths() -> list[str]:
    """Rutas de import para intérpretes hijos aislados (-I): paquete + rutas de confianza."""
    site = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # dir que contiene el paquete (o su .so)
    return [site] + [p for p in _trusted_sys_path() if p != site]


def ensure_isolated_interpreter(argv_tail: list[str]) -> None:
    """Reejecuta el intérprete en modo aislado (-I -B) con entorno saneado.

    Ignora PYTHONPATH/PYTHON*, cwd y user-site, y elimina LD_PRELOAD, QT_PLUGIN_PATH… (ver `clean_env`).
    Solo se conservan rutas de import de confianza (ver `_trusted_sys_path`).
    """
    if sys.flags.isolated or not sys.executable:
        return
    code = f"import sys; sys.path[:0] = {interpreter_paths()!r}; from tuxsign.app import main; raise SystemExit(main())"
    try:
        # sys.executable es el propio intérprete en ejecución y los argumentos no pasan por shell.
        os.execve(sys.executable, [sys.executable, "-I", "-B", "-c", code, *argv_tail], clean_env())  # nosec B606
    except OSError:
        pass  # si no se puede, se continúa sin aislamiento (best-effort)


def harden_process(worker: bool = False) -> dict[str, bool]:
    """Hardening best-effort. `worker=True`: perfil del proceso de render (sin ficheros, sin sockets, sin exec)."""
    report: dict[str, bool] = {}
    os.umask(0o077)
    report["umask_077"] = True
    try:
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        report["core_dumps_disabled"] = True
    except (ValueError, OSError):
        report["core_dumps_disabled"] = False
    report["isolated_interpreter"] = bool(sys.flags.isolated)
    try:
        libc = ctypes.CDLL(None, use_errno=True)
    except OSError:
        return report
    report["non_dumpable"] = libc.prctl(_PR_SET_DUMPABLE, 0, 0, 0, 0) == 0
    report["no_new_privs"] = libc.prctl(_PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) == 0
    if report["no_new_privs"]:
        report["landlock"] = _landlock(libc, fs=worker, net=True)
        report["seccomp_filter"] = _seccomp_install(libc, worker)
    else:
        report["landlock"] = report["seccomp_filter"] = False
    return report


def _landlock(libc: ctypes.CDLL, fs: bool, net: bool) -> bool:
    """Landlock sin reglas "allow": deniega TODO el acceso a ficheros (fs) y/o bind/connect TCP (net)."""
    try:
        abi = libc.syscall(_SYS_LANDLOCK_CREATE_RULESET, None, 0, _LANDLOCK_CREATE_RULESET_VERSION)
        if abi < (1 if fs else 4):
            return False
        fs_mask = 0
        if fs:
            fs_mask = (1 << 13) - 1                 # ABI 1: EXECUTE … MAKE_SYM
            fs_mask |= (1 << 13) if abi >= 2 else 0  # REFER
            fs_mask |= (1 << 14) if abi >= 3 else 0  # TRUNCATE
        net_mask = (_LANDLOCK_ACCESS_NET_BIND_TCP | _LANDLOCK_ACCESS_NET_CONNECT_TCP) if (net and abi >= 4) else 0

        class Attr(ctypes.Structure):
            _fields_ = [("handled_access_fs", ctypes.c_uint64), ("handled_access_net", ctypes.c_uint64)]

        attr = Attr(fs_mask, net_mask)
        size = ctypes.sizeof(attr) if abi >= 4 else 8  # el ABI 1-3 solo conoce handled_access_fs
        fd = libc.syscall(_SYS_LANDLOCK_CREATE_RULESET, ctypes.byref(attr), size, 0)
        if fd < 0:
            return False
        try:
            return libc.syscall(_SYS_LANDLOCK_RESTRICT_SELF, fd, 0) == 0
        finally:
            os.close(fd)
    except Exception:  # noqa: BLE001 - el hardening nunca debe impedir el arranque
        return False


# nº de syscall por arquitectura (denylist → EPERM)
_ARCH = {
    "x86_64": dict(
        audit=0xC000003E, seccomp=317, socket=41, x32=True, exec_=(59, 322), socketpair=53,
        deny=dict(ptrace=101, process_vm_readv=310, process_vm_writev=311, kexec_load=246, kexec_file_load=320,
                  mount=165, umount2=166, pivot_root=155, bpf=321, perf_event_open=298, userfaultfd=323,
                  keyctl=250, add_key=248, request_key=249, init_module=175, finit_module=313, delete_module=176,
                  reboot=169, swapon=167, swapoff=168, open_by_handle_at=304, kcmp=312),
    ),
    "aarch64": dict(
        audit=0xC00000B7, seccomp=277, socket=198, x32=False, exec_=(221, 281), socketpair=199,
        deny=dict(ptrace=117, process_vm_readv=270, process_vm_writev=271, kexec_load=104, kexec_file_load=294,
                  mount=40, umount2=39, pivot_root=41, bpf=280, perf_event_open=241, userfaultfd=282,
                  keyctl=219, add_key=217, request_key=218, init_module=105, finit_module=273, delete_module=106,
                  reboot=142, swapon=224, swapoff=225, open_by_handle_at=265, kcmp=272),
    ),
}
_AF_DENIED = (2, 10, 17)  # AF_INET, AF_INET6, AF_PACKET (se permite AF_UNIX: Wayland/X11/D-Bus)


def _seccomp_program(arch: dict, worker: bool = False) -> bytes:
    """Genera el BPF clásico del filtro (lista de bloqueo, arquitectura verificada)."""
    ALLOW, KILL = 0x7FFF0000, 0x80000000
    EPERM, EACCES = 0x00050000 | 1, 0x00050000 | 13
    ins: list[list] = []  # [code, jt, jf, k, jt_label, jf_label]

    def emit(code, k=0, jt=0, jf=0, jt_l=None, jf_l=None, label=None):
        ins.append([code, jt, jf, k, jt_l, jf_l, label])

    emit(0x20, 4)                                   # ld  arch
    emit(0x15, arch["audit"], jt=1)                 # jeq arch → salta KILL
    emit(0x06, KILL)                                # ret KILL (arquitectura inesperada)
    emit(0x20, 0)                                   # ld  nr
    if arch["x32"]:
        emit(0x35, 0x40000000, jf=1)                # jge x32-bit → KILL (evita bypass x32)
        emit(0x06, KILL)
    denied = list(arch["deny"].values())
    if worker:  # el proceso de render no necesita ejecutar programas ni crear sockets de ningún tipo
        denied += list(arch["exec_"]) + [arch["socket"], arch["socketpair"]]
    for nr in denied:
        emit(0x15, nr, jt_l="EPERM")
    if not worker:
        emit(0x15, arch["socket"], jt=1)            # ¿socket()? → bloque de dominios
        emit(0x06, ALLOW)
        emit(0x20, 16)                              # ld  args[0] (dominio)
        for af in _AF_DENIED:
            emit(0x15, af, jt_l="EACCES")
    emit(0x06, ALLOW)
    emit(0x06, EPERM, label="EPERM")
    emit(0x06, EACCES, label="EACCES")
    labels = {i[6]: n for n, i in enumerate(ins) if i[6]}
    out = b""
    for n, (code, jt, jf, k, jt_l, jf_l, _lab) in enumerate(ins):
        if jt_l:
            jt = labels[jt_l] - n - 1
        if jf_l:
            jf = labels[jf_l] - n - 1
        if not (0 <= jt < 256 and 0 <= jf < 256):
            raise ValueError("salto BPF fuera de rango")
        out += struct.pack("=HBBI", code, jt, jf, k)
    return out


def _seccomp_install(libc: ctypes.CDLL, worker: bool = False) -> bool:
    arch = _ARCH.get(platform.machine())
    if not arch or sys.byteorder != "little":
        return False
    try:
        prog = _seccomp_program(arch, worker)
        buf = ctypes.create_string_buffer(prog, len(prog))

        class Fprog(ctypes.Structure):
            _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.c_void_p)]

        fp = Fprog(len(prog) // 8, ctypes.cast(buf, ctypes.c_void_p))
        # SECCOMP_SET_MODE_FILTER=1, SECCOMP_FILTER_FLAG_TSYNC=1 (aplica a todos los hilos)
        return libc.syscall(arch["seccomp"], 1, 1, ctypes.byref(fp)) == 0
    except Exception:  # noqa: BLE001
        return False


# --------------------------------------------------------------------------- ficheros
def read_regular_file(path: str, max_bytes: int, magic: bytes | None = None) -> bytes:
    """Lee un fichero regular con límite de tamaño y sin FIFOs ni dispositivos (fstat sobre el fd, sin TOCTOU)."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK)
    except OSError as exc:
        raise InputRejected("err_open") from exc
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise InputRejected("err_not_regular")
        if st.st_size == 0 or st.st_size > max_bytes:
            raise InputRejected("err_size", mb=max_bytes // (1024 * 1024) or 1)
        with os.fdopen(fd, "rb", closefd=False) as fh:
            data = fh.read(max_bytes + 1)
    finally:
        os.close(fd)
    if len(data) > max_bytes:
        raise InputRejected("err_size", mb=max_bytes // (1024 * 1024) or 1)
    if magic and not data[:1024].lstrip(b"\x00 \t\r\n").startswith(magic):
        raise InputRejected("err_format")
    return data


def atomic_write(path: str, data: bytes, mode: int = 0o600) -> None:
    """Escritura atómica (tmp O_EXCL + fsync + rename)."""
    directory = os.path.dirname(os.path.abspath(path))
    tmp = os.path.join(directory, f".{os.path.basename(path)}.{os.getpid()}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC, mode)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


class Secret:
    """Secreto en un bytearray sobrescribible (Python no garantiza que no haya copias, ver SECURITY.md)."""

    __slots__ = ("_buf",)

    def __init__(self, text: str):
        self._buf = bytearray(text.encode("utf-8"))

    def reveal(self) -> bytes:
        return bytes(self._buf)

    def wipe(self) -> None:
        for i in range(len(self._buf)):
            self._buf[i] = 0
        self._buf.clear()

    def __repr__(self) -> str:  # nunca filtrar en logs
        return "Secret(***)"

    __str__ = __repr__


class AttemptLimiter:
    """Retardo exponencial tras fallos de autenticación (anti fuerza bruta local)."""

    def __init__(self, free_attempts: int = 3, base_delay: float = 2.0, max_delay: float = 300.0):
        self._fails = 0
        self._free = free_attempts
        self._base = base_delay
        self._max = max_delay
        self._locked_until = 0.0

    def remaining(self) -> float:
        return max(0.0, self._locked_until - time.monotonic())

    def failure(self) -> None:
        self._fails += 1
        if self._fails > self._free:
            delay = min(self._max, self._base * 2 ** (self._fails - self._free - 1))
            self._locked_until = time.monotonic() + delay

    def success(self) -> None:
        self._fails = 0
        self._locked_until = 0.0
