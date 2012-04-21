import subprocess
import os

from django.http import HttpResponse
from django.template.loader import render_to_string

def printtopdf(request, template, context, filename):

    # Determine whether wkhtmltopdf exists; die if it doesn't
    found = False
    pdf_converter_exe_name = "wkhtmltopdf"
    for path in os.environ["PATH"].split(os.pathsep):
        exe_path = os.path.join(path, pdf_converter_exe_name)
        if os.path.exists(exe_path) and os.access(exe_path, os.X_OK):
            found = True
    if not found:
        resp = HttpResponse(
            "No executable `" + pdf_converter_exe_name + "` found in PATH"
        )
        resp.status_code = 500
        return resp

    # Generate PDF
    resp = HttpResponse(
        subprocess.Popen(
            [pdf_converter_exe_name, "-", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        ).communicate(
            input=render_to_string(template, context)
        )[0],
        content_type="application/pdf"
    )
    resp["Content-Disposition"] = "attachment; filename=" + filename + ".pdf"
    return resp
