"""SkyStacker single-image filter presets exposed in the Filter menu."""

SKY_FILTERS = {
    "sky-blur": ("blur", ["--denoise-radius", "6"], "SkyStacker Blur"),
    "sky-blur-strong": ("blur", ["--denoise-radius", "12"], "SkyStacker Strong Blur"),
    "sky-unsharp": (
        "sharpen", ["--sharpen-amount", "1.2", "--sharpen-radius", "1.5"],
        "SkyStacker Unsharp Mask",
    ),
    "sky-unsharp-strong": (
        "sharpen", ["--sharpen-amount", "2.5", "--sharpen-radius", "2"],
        "SkyStacker Strong Unsharp",
    ),
    "sky-wave-sharpen": (
        "sharpen", ["--wavesharp", "--wave-gains", "0.25,0.15,0.08"],
        "SkyStacker Wavelet Sharpen",
    ),
    "sky-wave-sharpen-detail": (
        "sharpen", ["--wavesharp", "--wave-gains", "0.4,0.25,0.12"],
        "SkyStacker Wavelet Detail",
    ),
    "sky-bg-poly": ("background", ["--bg-degree", "2"], "SkyStacker Polynomial Background"),
    "sky-bg-mask": ("background", ["--mask-bg"], "SkyStacker Masked Background"),
    "sky-bg-multiscale": (
        "background", ["--bg-multiscale"], "SkyStacker Multiscale Background",
    ),
    "sky-bg-asymmetric": (
        "background",
        ["--bg-asymmetric", "--bg-clip-low", "3", "--bg-clip-high", "1.5"],
        "SkyStacker Asymmetric Background",
    ),
    "sky-bg-rbf": (
        "background", ["--bg-asymmetric", "--bg-rbf", "--bg-poly-degree", "4"],
        "SkyStacker RBF Background",
    ),
    "sky-stf": ("stretch", [], "SkyStacker Auto STF"),
    "sky-stf-linked": ("stretch", ["--stf-linked"], "SkyStacker Linked STF"),
    "sky-stf-neutral": (
        "stretch", ["--stf-shadows", "-3.5", "--stf-target", "0.35"],
        "SkyStacker Neutral STF",
    ),
    "sky-denoise": ("denoise", [], "SkyStacker Guided Denoise"),
    "sky-denoise-strong": (
        "denoise", ["--denoise-strength", "8", "--denoise-radius", "5"],
        "SkyStacker Strong Denoise",
    ),
    "sky-wavelet-denoise": (
        "denoise", ["--wavelets", "--wavelet-scales", "4", "--wavelet-sigma", "3"],
        "SkyStacker Wavelet Denoise",
    ),
    "sky-wavelet-denoise-adaptive": (
        "denoise", ["--wavelets", "--wavelet-adaptive"],
        "SkyStacker Adaptive Wavelet Denoise",
    ),
    "sky-deconv-rl": ("deconvolve", [], "SkyStacker Richardson-Lucy"),
    "sky-deconv-wiener": (
        "deconvolve", ["--deconvolve-wiener"], "SkyStacker Wiener Deconvolution",
    ),
    "sky-deconv-grid": (
        "deconvolve", ["--deconvolve-grid", "--deconv-grid-size", "3"],
        "SkyStacker Grid Deconvolution",
    ),
    "sky-starless": ("starless", [], "SkyStacker Starless"),
    "sky-starless-psf": ("starless", ["--starless-psf"], "SkyStacker PSF Starless"),
    "sky-starless-aggressive": (
        "starless", ["--star-sigma", "2.5", "--star-radius", "5"],
        "SkyStacker Aggressive Starless",
    ),
}

SKY_FILTER_MENU = (
    (
        "SkyStacker Blur & Sharpen",
        None,
        (
            ("Blur", "sky-blur"),
            ("Strong Blur", "sky-blur-strong"),
            (None, None),
            ("Unsharp Mask", "sky-unsharp"),
            ("Strong Unsharp", "sky-unsharp-strong"),
            ("Wavelet Sharpen", "sky-wave-sharpen"),
            ("Wavelet Detail", "sky-wave-sharpen-detail"),
        ),
    ),
    (
        "SkyStacker Background",
        None,
        (
            ("Polynomial Background", "sky-bg-poly"),
            ("Masked Background", "sky-bg-mask"),
            ("Multiscale Background", "sky-bg-multiscale"),
            ("Asymmetric Background", "sky-bg-asymmetric"),
            ("RBF Background", "sky-bg-rbf"),
        ),
    ),
    (
        "SkyStacker Stretch",
        None,
        (
            ("Auto STF", "sky-stf"),
            ("Linked STF", "sky-stf-linked"),
            ("Neutral STF", "sky-stf-neutral"),
        ),
    ),
    (
        "SkyStacker Denoise",
        None,
        (
            ("Guided Denoise", "sky-denoise"),
            ("Strong Denoise", "sky-denoise-strong"),
            ("Wavelet Denoise", "sky-wavelet-denoise"),
            ("Adaptive Wavelet Denoise", "sky-wavelet-denoise-adaptive"),
        ),
    ),
    (
        "SkyStacker Deconvolution",
        None,
        (
            ("Richardson-Lucy", "sky-deconv-rl"),
            ("Wiener Deconvolution", "sky-deconv-wiener"),
            ("Grid Deconvolution", "sky-deconv-grid"),
        ),
    ),
    (
        "SkyStacker Starless",
        None,
        (
            ("Starless", "sky-starless"),
            ("PSF Starless", "sky-starless-psf"),
            ("Aggressive Starless", "sky-starless-aggressive"),
        ),
    ),
)
