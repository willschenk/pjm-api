"""Generic template query — requires pjm-api init first."""

from pjm_api import CliBackend, load_settings
from pjm_api.templates import suggest_params


def main() -> None:
    params = suggest_params("TRANSSERV")
    backend = CliBackend(load_settings())
    result = backend.run_template(
        template="TRANSSERV",
        params=params,
        outfile="transserv.txt",
        print_results=True,
    )
    print("returncode:", result.returncode)
    print("output_file:", result.output_file)


if __name__ == "__main__":
    main()
