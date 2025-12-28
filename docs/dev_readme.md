```sh
ruff check . --fix
ruff format .

pytest
mypy src/ --config-file config/mypy.ini
```