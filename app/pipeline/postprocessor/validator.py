def validate_testcases(testcases):
    if not isinstance(testcases, list):
        return testcases

    for tc in testcases:
        # title
        if not tc.get("title"):
            tc["title"] = "Untitled Test Case"

        # preconditions
        if not tc.get("preconditions"):
            tc["preconditions"] = ["Tidak ada precondition khusus"]

        # steps
        if not tc.get("steps"):
            tc["steps"] = ["Lakukan aksi sesuai skenario"]

        # expected result
        if not tc.get("expected_result"):
            tc["expected_result"] = ["Sistem merespons sesuai ekspektasi"]

    return testcases
