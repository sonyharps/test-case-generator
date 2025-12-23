def validate_testcases(testcases):
    if not isinstance(testcases, list):
        return

    for tc in testcases:
        if not tc.get("tc_id"):
            raise ValueError("Test case missing tc_id")

        if not tc.get("title"):
            tc["title"] = "Untitled Test Case"

        if not tc.get("steps"):
            tc["steps"] = ["Lakukan aksi sesuai skenario"]

        if not tc.get("expected_result"):
            tc["expected_result"] = ["Sistem merespons sesuai ekspektasi"]
