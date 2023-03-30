"""
Purpose: Compute Jadud's error quotient (EQ) for every student based on their compilation logs and errors.

Input/prerequisites: 2 CSV files, one with all compilation events, the other with all compilation errors. Join attribute: student_id.
Output: Jadud's EQ for every individual student_id in the logs.

Author: Valdemar Švábenský <valdemar@upenn.edu>, University of Pennsylvania, 2023.
Reviewed by: TODO: We need to assign a code reviewer.
License: MIT.

===== UNIT TEST DOCUMENTATION =====

For testing, use the files 'hwtestfile-complete_snapshots.csv' and 'hwtestfile-compiler-errors.csv'.
The files were designed as follows:

Student A compiled at times 3, 4. Made no errors.
Student B compiled at times 1, 3, 5. Made errors in 1, 5 (not consecutive, different error types).
Student C compiled at times 1, 3, 4. Made errors in 1, 4 (not consecutive, same error types).
Student D compiled at times 5, 6. Made errors in 5, 6 (consecutive, different error types).
Student E compiled at times 4, 5. Made errors in 4, 5 (consecutive, same error types).
Student F compiled at times 1, 3, 4. Made errors in 1, 3, 4 (consecutive, first pair same error, second pair same error).
Student G compiled at times 1, 3, 4. Made errors in 1, 3, 4 (consecutive, first pair same error, second pair different error).
Student H compiled at times 1, 3, 4. Made errors in 1, 3, 4 (consecutive, first pair different error, second pair same error).
Student I compiled at times 1, 3, 4. Made errors in 1, 3, 4 (consecutive, first pair different error, second pair different error).

Expected output for the Jadud's EQ:
A 0.0
B 0.0
C 0.0
D 0.7272727272727273
E 1.0
F 1.0
G 0.8636363636363636
H 0.8636363636363636
I 0.7272727272727273
"""

import csv


def process_data_errors(hw_name='03'):
    """
    Read a single CSV file from the folder `data-errors` for one particular homework,
    and process this file to represent it in a dictionary with the following structure:
    { student_id : { timestamp : [error_types] } }, where all entries are of type str.
    This dictionary represents all compiler error types a given student made at a given time.

    For example:
    {
        'student_A' : { 't1' : ['error_X', 'error_Y'] }
        'student_B' : { 't1' : ['error_X', 'error_X', 'error_Z'], 't2' : ['error_Y'] }
    }

    :param hw_name: str. Number of the homework assignment.
    :return: dict. Dictionary with the structure described above.
    """
    filename = 'data-errors/hw' + hw_name + '-compiler-errors.csv'
    file_handle = open(filename, encoding='latin-1')
    reader = csv.reader(file_handle, delimiter=';')
    next(reader)  # Skip the CSV header
    all_errors = {}  # The dictionary
    for row in reader:
        student_id, timestamp, error_message = row[0], row[1], row[4]
        timestamp = timestamp.replace('_', ':')  # For compatibility with the different timestamp format in the snapshots file
        linebreak_index_in_error_message = error_message.find('\n')  # The messages span multiple lines, we want only the first line
        if linebreak_index_in_error_message == -1:
            linebreak_index_in_error_message = len(error_message)
        error_type = error_message[:linebreak_index_in_error_message].strip()
        if student_id not in all_errors:
            all_errors[student_id] = {}
            all_errors[student_id][timestamp] = [error_type]
        elif timestamp not in all_errors[student_id]:
            all_errors[student_id][timestamp] = [error_type]
        else:
            all_errors[student_id][timestamp].append(error_type)
    file_handle.close()
    return all_errors


def process_data_snapshots(hw_name='03'):
    """
    Read a single CSV file from the folder `data-snapshots` for one particular homework,
    and process this file to represent it in a dictionary with the following structure:
    { student_id : [compilation_events] }, where:
        * student_id is of type str, and
        * [compilation_events] is a list of lists representing compilation events, where:
            * [] is a successful compilation event (without any errors), and
            * a non-empty list contains strings that indicate error types occurring during that compilation event.
    Together, each list represents the whole student compilation session.

    For example:
    {
        'student_A' : [ ['error_X', 'error_Y'], [], [] ]
        'student_B' : [ ['error_X', 'error_X', 'error_Z'], ['error_Y'], [], [], ['error_Z'] ]
    }

    :param hw_name: str. Number of the homework assignment.
    :return: dict. Dictionary with the structure described above.
    """
    all_errors = process_data_errors(hw_name)
    filename = 'data-snapshots/hw' + hw_name + '-complete_snapshots.csv'
    file_handle = open(filename)
    reader = csv.reader(file_handle, delimiter=';')
    next(reader)  # Skip the CSV header
    all_students = {}  # The dictionary
    for row in reader:
        student_id, timestamp = row[0], row[1]
        errors = []  # Empty list indicates a successful compilation event (i.e., no errors)
        if student_id in all_errors and timestamp in all_errors[student_id]:  # all_errors is used only at this place
            errors = all_errors[student_id][timestamp]  # This student made 1 or more errors during this timestamp
        if student_id not in all_students:
            all_students[student_id] = []
        all_students[student_id].append(errors)
    file_handle.close()
    return all_students


def compute_jadud_eq(hw_name='03'):
    """
    Calculate the Jadud's error quotient (EQ) for each student in the logs for the given homework files.
    The algorithm is described in the following publication on page 6:
        Matthew C. Jadud. 2006. Methods and tools for exploring novice compilation behaviour.
        In Proceedings of the second international workshop on Computing education research (ICER '06).
        ACM, New York, NY, USA, 73–84. https://dl.acm.org/doi/pdf/10.1145/1151588.1151600

    Then, print the student_id with their error quotient, for example:
        008a13042777e1aaca446a68fbc5b3877e6ed232 0.17272727272727273
        0106f488719b5b6dec8020fdf6c9e2e6d2059227 0.07142857142857142
        025e11c5a647be6af45e5040241901ecd65080f3 0.0

    :param hw_name: str. Number of the homework assignment.
    :return: None.
    """
    all_students = process_data_snapshots(hw_name)
    for student_id, student_session in all_students.items():
        student_total_eq = 0
        num_event_pairs_per_student = 0
        for i in range(len(student_session) - 1):  # 1. COLLATE: Create consecutive pairs from the events in the session
            num_event_pairs_per_student += 1
            current_event_errors = set(student_session[i])  # Create a set to ignore multiple errors of the same type
            next_event_errors = set(student_session[i+1])

            eq_per_event_pair = 0  # Error score (quotient) for the pair of the current and next event
            if current_event_errors and next_event_errors:  # 2. CALCULATE: Score the event pair according to the algorithm
                eq_per_event_pair += 8  # Both events ended in (at least one) error
                if not current_event_errors.isdisjoint(next_event_errors):
                    eq_per_event_pair += 3  # Both events included the same error type
                eq_per_event_pair /= 11  # 3. NORMALIZE: Divide the score assigned to each pair by 11

            student_total_eq += eq_per_event_pair  # 4a. AVERAGE: Sum the scores...

        assert num_event_pairs_per_student > 0, 'This should not happen because it indicates no compilation events.'
        student_total_eq /= num_event_pairs_per_student  # 4b. AVERAGE: ... and divide by the number of pairs
        assert 0 <= student_total_eq <= 1, 'The EQ must be between 0 and 1'
        print(student_id, student_total_eq)


if __name__ == '__main__':
    for hw in ['testfile', '03', '04', '05', '06', '07', '08']:
        compute_jadud_eq(hw)
