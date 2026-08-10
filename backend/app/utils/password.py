from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# One hasher instance, reused for the process lifetime. Its defaults
# (time cost, memory cost, parallelism) are Argon2id with OWASP-recommended
# parameters - deliberately slow, which is the entire point.
_hasher = PasswordHasher()


def hash_password(plain_password: str) -> str:
    """
    Turns a plaintext password into a one-way Argon2id hash.
    The output string embeds the algorithm + parameters used, so we can
    change hashing parameters later without breaking old hashes.
    """
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Re-hashes the candidate password with the same parameters stored in
    `hashed_password` and compares - never by reversing the hash (impossible),
    only by forward-checking.
    """
    try:
        return _hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
