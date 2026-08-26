def validate_testcases(testcases):
    if not isinstance(testcases, list):
        return testcases

    for tc in testcases:
        # title
        if not tc.get("title"):
            tc["title"] = "Untitled Test Case"

        # priority (ISO/IEC/IEEE 29119-3)
        if not tc.get("priority"):
            tc["priority"] = "P2"

        # module
        if not tc.get("module"):
            tc["module"] = "General"

        # preconditions
        if not tc.get("preconditions"):
            tc["preconditions"] = ["Tidak ada precondition khusus"]

        # test_data (ISO/IEC/IEEE 29119-3)
        if not tc.get("test_data"):
            tc["test_data"] = []

        # steps
        if not tc.get("steps"):
            tc["steps"] = ["Lakukan aksi sesuai skenario"]

        # expected result
        if not tc.get("expected_result"):
            tc["expected_result"] = ["Sistem merespons sesuai ekspektasi"]

        # postconditions (ISO/IEC/IEEE 29119-3)
        if not tc.get("postconditions"):
            tc["postconditions"] = []

    return testcases
