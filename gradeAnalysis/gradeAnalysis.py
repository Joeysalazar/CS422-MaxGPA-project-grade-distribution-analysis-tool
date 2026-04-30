import csv
from collections import defaultdict
import os

#load data section
#========================================

#Load raw CSV data using DictReader
def load_csv_data(filename):
    #use handler-based parsing instead of hardcoding column indices
    #ensures compatibility with different CSV formats
    #keeps ingestion separte from transformation
    with open(filename, newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)

#load degree plan from CSV
def load_degree_plan(filepath):
    #keeps degree data seperate from grade-history data
    plan = []
    with open(filepath, newline='') as f:
        reader = csv.DictReader(f)
        #print("HEADERS:", reader.fieldnames)
        for row in reader:

            numb = row['NUMB'].strip()

            plan.append({
                'year': int(row['YEAR']),
                'term': int(row['TERM']),
                'course_id': f"{row['SUBJ'].strip()}{numb}",
                'title': row['TITLE'].strip()
            })
    return plan

#Data Filtering
#===================================================

#filter grade data by year range
def filter_year(rows, start_year, end_year):
    #supports user requirement to select any span of years
    #uses TERM column (YYYY format) for filtering
    filtered = []
    for row in rows: 
        term_desc = row.get('TERM', '')

        parts = term_desc.strip().split()
        if len(parts) == 2 and parts[1].isdigit():
            year = int(parts[1])

            if start_year <= year <= end_year:
                filtered.append(row)

    return filtered

def make_course_id(subj, numb):
    subj = subj.strip().upper().replace(" ", " ")

    numb = ''.join(filter(str.isdigit, numb))
    return f"{subj}{numb}"

#Analytics Layer
#===================================================

#helper
def safe_int(x):
    try:
        return int(x)
    except:
        return 0
    
#categorize raw grade into A/B/C/DNF categories
def categorize_grade(grade):
    #implement requirement for grouping +/- grades
    #ensures consistent aggregation across datasets
    if not grade or grade == '*':
            return None
    
    grade = grade.strip().upper()

    #sort grade into distribution
    if grade.startswith('A'):
        return 'A'
    elif grade.startswith('B'):
        return 'B'
    elif grade.startswith('C'):
        return 'C'
    elif grade.startswith(('D', 'F', 'N')):
        return 'DNF'
    else:
        return None

#compute grade distribution for a course
def compute_grade_distribution(rows):
    #Input data already contains counts
    # must aggregate counts before computing percentages
    #matches specification: use all students, not averages

    #compute distribution from 'Grades' collumn
    counts = {'A': 0, 'B': 0, 'C': 0, 'DNF': 0}
    total = 0
    valid = False

    for row in rows:
        #skip fully redacted rows
        if row.get('TOT_NON_W', '0') == '0':
            valid = True

        try:
            #A+/-
            a_total = safe_int(row.get('AP')) + safe_int(row.get('A')) + safe_int(row.get('AM'))

            #B+/-
            b_total = safe_int(row.get('BP')) + safe_int(row.get('B')) + safe_int(row.get('BM'))

            #C+/-
            c_total = safe_int(row.get('CP')) + safe_int(row.get('C')) + safe_int(row.get('CM'))

            #DNF
            dnf_total = safe_int(row.get('DP')) + safe_int(row.get('D')) + safe_int(row.get('DM')) + safe_int(row.get('F')) + safe_int(row.get('N'))

        #skip bad rows safely
        except ValueError:
            continue

        counts['A'] += a_total
        counts['B'] += b_total
        counts['C'] += c_total
        counts['DNF'] += dnf_total

        total += (a_total + b_total + c_total + dnf_total)

    if not valid:
        return {"NO_DATA": True}

    if total == 0:
        return counts
    
    if a_total + b_total + c_total + dnf_total > 0:
        valid = True

    return {k: round((v/total) * 100, 2) for k, v in counts.items()}

#group grade data by course
def group_by_course(rows):
    #required to compute per-course distribution
    #uses normalized course identifiers
    courses = defaultdict(list)

    for row in rows:
        subj = row.get('SUBJ', '').strip()
        numb = row.get('NUMB', '').strip()

        if not subj or not numb:
            continue

        course_id = make_course_id(subj, numb)
        courses[course_id].append(row)

    return courses

#compute grade distribution per instructor
def instructor_distribution(rows):
    #enables instructor comparison feature
    #supports "find best instructor" requirement

    #get instructor data
    instructors = defaultdict(list)
    for row in rows:
        instructor = row.get('INSTRUCTOR', 'UNKNOWN')
        instructors[instructor].append(row)

    results = {}
    for inst, inst_rows in instructors.items():
        results[inst] = compute_grade_distribution(inst_rows)

    return results

#rank instructors by highest percentage of A grades
def rank_instructionors(distributions):
    #directly supports decision-making for students
    #simple and interpretable ranking metric

    #skip instructors with missing data
    valid = [
        (inst, dist)
        for inst, dist in distributions.items()
        if isinstance(dist, dict) and 'A' in dist
    ]

    #rank instructors based on distribution
    return sorted(
    valid,
    key=lambda x: x[1].get('A', 0),
    reverse=True
)


#Integration Layer
#===================================================

#match required courses to computed analytics
def match_degree_to_data(degree_plan, course_data):
    #ensures all required courses appear in output
    #handles missing data gracefully
    
    report = []
    for course in degree_plan:
        cid = course['course_id']

        #print("\n--- DEGREE PLAN IDS ---")
        #for c in degree_plan[:10]:
            #print(c['course_id'])

        if cid in course_data:
            report.append({
                'course': cid,
                'year': course['year'],
                'term': course['term'],
                'distribution': course_data[cid]['overall'],
                'instructors': course_data[cid]['instructors']
            })
        else:
            report.append({
                'course': cid,
                'year': course['year'],
                'term': course['term'],
                'missing': True,'no_data': True
            })

    return report

#full analytics pipeline
def run_analysis(grade_file, degree_file, start, end):
    #seperates pipeline stages clearly
    #supports independent updates of datasets
    grades = load_csv_data(grade_file)
    #recon = normalize_data(recon_file)
    degree_plan = load_degree_plan(degree_file)
    #print("Loaded rows:", len(grades))


    #grades = apply_normalization(grades)
    grades = filter_year(grades, start, end)

    course_groups = group_by_course(grades)

    print("Number of grouped courses:", len(course_groups))
    print("Sample course IDs:", list(course_groups.keys())[:10])


    course_results = {}
    for cid, rows in course_groups.items():
        course_results[cid] = {
            "overall": compute_grade_distribution(rows),
            "instructors": instructor_distribution(rows)
        }

    #match degree plan
    report = match_degree_to_data(degree_plan, course_results)
    return report

#User Interface
#===================================================

#helper
def find_degree_file(choice):
    base_dir = "data/degree_plans/matched/"

    #normalize input
    normalized = choice.lower().replace(" ", "_")

    for filename in os.listdir(base_dir):
        if normalized in filename.lower() and filename.endswith('.csv'):
            return os.path.join(base_dir, filename)
        
    return None

def main():
    files = {
        "Architecture": "data/degree_plans/matched/architecture_barch_matched_report.csv",
        "Computer Science": "data/degree_plans/matched/computer_science_bs_matched_report.csv",
        "Psychology": "data/degree_plans/matched/psychology_ba_matched_report.csv"
    }

    print("Avalilable majors: ")
    for key in files:
        print("-", key)

    choice = input("Choose major: ").strip()
    degree_file = find_degree_file(choice)

    if degree_file:
        start = int(input("Start year(e.g., 2016): "))
        end = int(input("End year(e.g., 2025): "))

        results = run_analysis(
            grade_file = "data/raw/pub_rec_master_w2016-f2025.csv",
            degree_file = find_degree_file(choice),
            #recon_file = "data/",
            start = start,
            end = end
        )
        
        for entry in results:
            print(f"\n{entry['course']}")

            if entry.get('missing'):
                print("Missing data for this course.")
            elif entry.get('no_data'):
                print("No data available for this course.")
            else:
                print(f"Overall: {entry['distribution']}")

                instructors = entry.get('instructors', {})

                if instructors:
                    ranked = rank_instructionors(instructors)

                    if ranked:
                        print("Top Instructor:", ranked[0])

    else:
        print("Invalid choice of file not found. Please choose from:")
        for key in files:
            print("-", key)

if __name__ == "__main__":
    main()