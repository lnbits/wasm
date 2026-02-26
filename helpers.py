from lnbits.helpers import template_renderer


def wasm_renderer():
    return template_renderer(["wasm/templates"])
