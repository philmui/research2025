##################################################################
# main.py
#
# This file is the main entry point for the application.
# 
# @author: Theodore Mui
# @version: 1.0
# @since: 2025-05-03
#
##################################################################

from app import app  # noqa: F401
import routes  # noqa: F401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
