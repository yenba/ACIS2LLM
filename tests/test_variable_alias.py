from acis2llm.composites import frequency_of_occurrence

def test_variable_alias_works_as_parameter():
    # If variable is supplied, it acts as parameter.
    try:
        frequency_of_occurrence(station="KNYC", variable="tmax", threshold=90, comparison=">=", month=7, start_year=2020, end_year=2021)
        assert True
    except TypeError as e:
        assert False, f"Should not raise TypeError: {e}"

