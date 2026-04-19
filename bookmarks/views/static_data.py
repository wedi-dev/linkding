import os

from django.conf import settings
from django.http import FileResponse, Http404


def data_static(request, filename: str):
    """Serve runtime-generated files (favicons, preview images) under /static/.

    WhiteNoise handles collected static assets from STATIC_ROOT; requests it can't
    satisfy fall through to this view, which searches the data/ subfolders.
    """
    if ".." in filename or filename.startswith("/"):
        raise Http404

    for folder in (settings.LD_FAVICON_FOLDER, settings.LD_PREVIEW_FOLDER):
        path = os.path.join(folder, filename)
        if os.path.isfile(path):
            return FileResponse(open(path, "rb"))  # noqa: SIM115

    raise Http404
