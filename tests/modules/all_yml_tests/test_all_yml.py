# Standard library imports
import os
import subprocess

# Third party imports
import pandas as pd
from colorama import Fore, Style
from colorama import init as colorama_init

colorama_init()


def run_yaml_files(root_directory):
    folders = []
    filenames = []
    statuses = []
    processed_files = set()

    for root, _dirs, files in os.walk(root_directory):
        # Skip files in the root directory and results subfolders
        if root == root_directory or "results" in root.split(os.sep):
            continue

        for filename in files:
            if filename.endswith((".yml", ".yaml")) and not filename.lower().startswith(
                "app"
            ):
                if filename in processed_files:
                    continue

                file_path = os.path.join(root, filename)
                try:
                    result = subprocess.run(
                        ["python", "-m", library, file_path],
                        check=True,
                        capture_output=True,
                    )
                    print(result.stdout.decode())
                    folders.append(os.path.relpath(root, root_directory))
                    filenames.append(filename)
                    statuses.append("Success")
                except subprocess.CalledProcessError as e:
                    print(e.stderr.decode())
                    folders.append(os.path.relpath(root, root_directory))
                    filenames.append(filename)
                    statuses.append("Failed")

                processed_files.add(filename)

        df = pd.DataFrame(
            {"Folder": folders, "Filename": filenames, "Status": statuses}
        )

        df = df.sort_values(by=["Status", "Folder"], ascending=[False, True])

        dir_path = os.path.dirname(os.path.abspath(__file__))

        df.to_csv(f"{dir_path}/repo_yml_status.csv", index=False)

    no_of_files = len(filenames)
    tests_passed = len(df[df["Status"] == "Success"])
    tests_failed = len(df[df["Status"] == "Failed"])

    summary_output = (
        f"Detailed output: {df}\n"
        f"No. of files processed: {no_of_files}\n"
        f"Tests passed: {tests_passed}\n"
        f"Tests Failed: {tests_failed}\n"
    )

    os.makedirs(dir_path, exist_ok=True)
    summary_file = os.path.join(dir_path, "yml_summary_pytest.txt")
    with open(summary_file, "w") as f:
        f.write(summary_output)

    print(f"Detailed output: {df}")
    print(f"No. of files processed: {len(filenames)}")
    print(
        f"Tests passed: {Fore.GREEN}{len(df[df['Status'] == 'Success'])}{Style.RESET_ALL}"
    )

    print(
        f"Tests Failed: {Fore.RED}{len(df[df['Status'] == 'Failed'])}{Style.RESET_ALL}"
    )
    print("Done !")


if __name__ == "__main__":
    library = "assetutilities"
    root_directory = "tests"
    run_yaml_files(root_directory)
