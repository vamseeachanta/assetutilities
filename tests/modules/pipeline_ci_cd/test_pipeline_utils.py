import pandas as pd


def test_pipeline():
    root_directory = "tests"
    repo_yml_status_csv = f"{root_directory}/modules/all_yml_tests/repo_yml_status.csv"
    summary_file = f"{root_directory}/modules/all_yml_tests/yml_summary_pytest.txt"

    df = pd.read_csv(repo_yml_status_csv)
    tests_expected = len(df[df["Status"] == "Success"])

    with open(summary_file) as file:
        content = file.read()

    tests_passed = None
    for line in content.splitlines():
        if "Tests passed:" in line:
            tests_passed = int(line.split(":")[1].strip())
            break

    assert tests_expected == tests_passed, (
        f"Mismatch in tests passed: expected ({tests_expected}) != original ({tests_passed})"
    )
