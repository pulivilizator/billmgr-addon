# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# """
# Пример WSGI файла

# """

# from pathlib import Path

# from billmgr_addon import create_wsgi_app

# plugin_path = Path(__file__).parent

# app = create_wsgi_app(
#     plugin_name="example_plugin",
#     plugin_path=plugin_path,
#     config_path=plugin_path / "config.toml",
# )


# if __name__ == "__main__":
#     flask_app = app.create_app()
#     flask_app.run(
#         host="127.0.0.1",
#         port=8000,
#         debug=True,
#         use_reloader=False,
#     )
