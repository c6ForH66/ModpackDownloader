k = 1 << 10
m = 1 << 20
g = 1 << 30
t = 1 << 40


def format_size(size: float | int) -> str:
    """Format a size (in bytes) to string"""

    if size < 0:
        raise ValueError(f"size cannot be negative: {size}")
    if size < 1 * k:
        return f"{size:.2f} B"
    if 1 * k <= size < 1 * m:
        return f"{size / k:.2f} KB"
    if 1 * m <= size < 1 * g:
        return f"{size / m:.2f} MB"
    if 1 * g <= size < 1 * t:
        return f"{size / g:.2f} GB"

    return f"{size / t:.2f} TB"
