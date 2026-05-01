import csv
from collections import defaultdict
import os

#global
recon_map = {}

#load data section
#========================================

#Load raw CSV data using DictReader
def load_csv_data(filename):
    #use handler-based parsing instead of hardcoding column indices
    #ensures compatibility with different CSV formats
    #keeps ingestion separte from transformation
    #print("Trying to load:", filename)

    with open(filename, newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    #print("Loaded rows from file:", len(rows))
    #print("Headers:", reader.fieldnames)

    return rows

#load degree plan from CSV
def load_degree_plan(filepath, recon_map):
    plan = []

    with open(filepath, newline='') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # normalize all possible column variants once
            subj = row.get('SUBJ', '').strip() or row.get('subj', '').strip()
            num = row.get('NUMB', '').strip() or row.get('num', '').strip()

            title = (
                row.get('DEGREE_TITLE', '') or
                row.get('INVENTORY_TITLE', '') or
                row.get('TITLE', '') or
                row.get('title', '')
            ).strip()

            year_raw = row.get('YEAR', '') or row.get('year', '')
            term_raw = row.get('TERM', '') or row.get('term', '')

            try:
                year = int(year_raw)
                term = int(term_raw)
            except:
                continue

            # DEBUG (temporary but useful)
            # print("PARSED:", subj, num, title, year, term)

            if not subj or not num:
                continue

            if not is_required(subj, num, title):
                continue

            plan.append({
                'year': year,
                'term': term,
                'course_id': make_course_id(subj, num),
                'title': reconcile(title, recon_map)
            })

    return plan

#loads reconciliation mapping from csv
#if file doesn't exist, return empty dict
def load_reconciliation(filepath):
    recon = {}

    if not os.path.exists(filepath):
        return recon
    
    with open(filepath, newline='')as f:
        reader = csv.DictReader(f)
        for row in reader:
            frm = row.get("CHANGE_FROM", "").strip()
            to = row.get("TO", "").strip()

            if frm and to:
                recon[frm.lower()] = to

    return recon

#Data Filtering
#===================================================

#filter for electives
def is_required(subj, num, title):
    if num.startswith("199"):
        return False
    
    if "special studies" in title.lower():
        return False
    
    return True

#check for asterisks only
def is_asterisk(rows):
    grade_keys = ["ap", "a", "am", "bp", "b", "bm", "cp", "c", "cm", "dp", "d", "dm", "f", "p", "n"]

    for row in rows:
        for key in grade_keys:
            v = row.get(key)
            if v not in (None, "", "*"):
                return False
    
    return True

#filter grade data by year range
def filter_year(rows, start_year, end_year):
    #supports user requirement to select any span of years
    #uses TERM column (YYYY format) for filtering
    filtered = []

    for row in rows: 
        term = row.get('term', '').strip()

        year = None

        parts = term.split()
        if len(parts) == 2 and parts[1].isdigit():
            year = int(parts[1])
        elif term.isdigit() and len(term) >= 4:
            year = int(term[:4])

        if year and start_year <= year <= end_year:
            filtered.append(row)

    return filtered

def make_course_id(subj, num):
    subj = subj.strip().upper().replace(" ", "")
    num = ''.join(filter(str.isdigit, num))
    return f"{subj}{num}"

#normalize str using recon mapping
#case insensitive
def reconcile(value, recon_map):
    if not value:
        return value
    
    v = value.strip().lower()
    return recon_map.get(v, value.strip())

def normalize_grade_row(row, recon_map):
    subj = row.get('subj', '').strip()
    num = row.get('num', '').strip()
    title = row.get('title', '').strip()

    # apply reconciliation to title
    title = reconcile(title, recon_map)

    # normalize course ID
    course_id = make_course_id(subj, num)

    return course_id, title

#Analytics Layer
#===================================================

#helper
def safe_int(x):
    try:
        if x is None:
            return 0
        x = str(x).strip()
        if x == "" or x == "*":
            return 0
        return int(x)
    except:
        return 0

#compute grade distribution for a course
def compute_grade_distribution(rows):
    #Input data already contains counts
    # must aggregate counts before computing percentages
    #matches specification: use all students, not averages

    #compute distribution from 'Grades' collumn
    counts = {'A': 0, 'B': 0, 'C': 0, 'DNF': 0, 'Pass': 0}
    total = 0

    if is_asterisk(rows):
        return{
            "A": 0.0,
            "B": 0.0,
            "C": 0.0,
            "DNF": 0.0,
            "Pass": 0.0,
            "total_students": 0,
            "has_data": False,
            "asterisk_only": True
        }

    for row in rows:
        try:
            a_total = safe_int(row.get('AP', 0)) + safe_int(row.get('A', 0)) + safe_int(row.get('AM', 0))
            b_total = safe_int(row.get('BP', 0)) + safe_int(row.get('B', 0)) + safe_int(row.get('BM', 0))
            c_total = safe_int(row.get('CP', 0)) + safe_int(row.get('C', 0)) + safe_int(row.get('CM', 0))
            dnf_total = (
                safe_int(row.get('DP', 0)) + 
                safe_int(row.get('D', 0)) + 
                safe_int(row.get('DM', 0)) + 
                safe_int(row.get('F', 0)) + 
                safe_int(row.get('N', 0)))
            pass_total = safe_int(row.get('P', 0))

        #skip bad rows safely
        except Exception:
            continue

        row_total = a_total + b_total + c_total + dnf_total + pass_total


        counts['A'] += a_total
        counts['B'] += b_total
        counts['C'] += c_total
        counts['DNF'] += dnf_total
        counts['Pass'] += pass_total

        total += row_total

    if total == 0:
        return{
            "A": 0.0,
            "B": 0.0,
            "C": 0.0,
            "DNF": 0.0,
            "Pass": 0.0,
            "total_students": 0,
            "has_data": False
        }
    
    return{
        "A": round((counts["A"] / total) * 100, 2),
        "B": round((counts["B"] / total) * 100, 2),
        "C": round((counts["C"] / total) * 100, 2),
        "DNF": round((counts["DNF"] / total) * 100, 2),
        "Pass": round((counts["Pass"] / total) * 100, 2),
        "total_students": total,
        "has_data": True
    }

#group grade data by course
def group_by_course(rows, recon_map):
    #required to compute per-course distribution
    #uses normalized course identifiers
    courses = defaultdict(list)

    for row in rows:
        subj = row.get('subj', '').strip()
        num = row.get('num', '').strip()

        if not subj or not num:
            continue

        course_id, title = normalize_grade_row(row, recon_map)

        row['title'] = title
        courses[course_id].append(row)

    return courses

#compute grade distribution per instructor
def instructor_distribution(rows):
    #enables instructor comparison feature
    #supports "find best instructor" requirement

    #get instructor data
    instructors = defaultdict(list)
    for row in rows:
        instructor = row.get('instructor', 'UNKNOWN')
        instructors[instructor].append(row)

    results = {}
    for inst, inst_rows in instructors.items():
        results[inst] = compute_grade_distribution(inst_rows)

    return results

#rank instructors by highest percentage of A grades
def rank_instructors(distributions):
    #directly supports decision-making for students
    #simple and interpretable ranking metric

    #skip instructors with missing data
    ranked = []

    for inst, dist in distributions.items():
        if not isinstance(dist, dict):
            continue

        a = dist.get("A", 0)
        dnf = dist.get("DNF", 0)
        pss = dist.get("Pass", 0)
        total = dist.get("total_students", 0)

        #skip empty entries
        if total == 0:
            continue

        ranked.append({
            "instructor": inst,
            "A": a,
            "Pass": pss,
            "DNF": dnf,
            "total": total
        })

    #sorting logic
    #1. highest A or pass
    #2. lowest DNF
    #3. highest sample size
    ranked.sort(
        key=lambda x: (
            -x["A"],
            -x["Pass"],
            x["DNF"],
            -x["total"]
        )
    )

    return ranked


#Integration Layer
#===================================================

#compute distributions to instructor
def instructor_distributions(instructor_index):
    results = {}

    for inst, rows in instructor_index.items():
        results[inst] = compute_grade_distribution(rows)

    return results

#match required courses to computed analytics
def match_degree_to_data(degree_plan, course_data):
    #ensures all required courses appear in output
    #handles missing data gracefully
    
    report = []
    for course in degree_plan:
        cid = course['course_id']

        if cid in course_data:
            course_entry = course_data[cid]

            # detect asterisk-only case
            if course_entry.get("overall", {}).get("asterisk_only", False):
                report.append({
                    'course': cid,
                    'year': course['year'],
                    'term': course['term'],
                    'asterisk_only': True,
                    'no_data': True
                })
            else:
                report.append({
                    'course': cid,
                    'year': course['year'],
                    'term': course['term'],
                    'distribution': course_entry['overall'],
                    'instructors': course_entry['instructors']
                })

        else:
            report.append({
                'course': cid,
                'year': course['year'],
                'term': course['term'],
                'missing': True,
                'no_data': True
            })

    return report

#full analytics pipeline
def run_analysis(grade_file, degree_file, start, end, recon_map):
    #seperates pipeline stages clearly
    #supports independent updates of datasets
    grades = load_csv_data("data/grades/cleaned_pub_rec_master.csv")
    degree_plan = load_degree_plan(degree_file, recon_map)
    
    grade = filter_year(grades, start, end)

    course_groups = group_by_course(grades, recon_map)
    course_instructors_map = defaultdict(lambda: defaultdict(list))

    for row in grades:
        cid, _ = normalize_grade_row(row, recon_map)

        if cid not in course_groups:
            continue

        inst = row.get('instructor', 'UNKNOWN').strip()
        course_instructors_map[cid][inst].append(row)

    course_results = {}

    for cid, rows in course_groups.items():

        inst_rows = course_instructors_map.get(cid, {})

        course_instructors = {
            inst: compute_grade_distribution(inst_rows_list)
            for inst, inst_rows_list in inst_rows.items()
        }

        course_results[cid] = {
            "overall": compute_grade_distribution(rows),
            "instructors": course_instructors
        }

    #match degree plan
    report = match_degree_to_data(degree_plan, course_results)
    print("TOTAL GRADES LOADED:", len(grades))
    print("COURSE GROUPS:", len(course_groups))
    print("DEGREE PLAN SIZE:", len(degree_plan))
    return report

#User Interface
#===================================================

def main():
    global recon_map
    recon_map = load_reconciliation("data/reconciliation.csv")

    choice = input("Choose major: ").strip().lower()

    files = {
        "architecture": "data/degree_plans/matched/architecture_barch_match_report.csv",
        "computer science": "data/degree_plans/matched/computer_science_bs_match_report.csv",
        "psychology": "data/degree_plans/matched/psychology_ba_match_report.csv"
    }

    degree_file = files.get(choice)

    if not degree_file:
        print("Invalid choice.")
        return
    
    try:
        start = int(input("Start year (e.g., 2016): "))
        end = int(input("End year (e.g., 2025): "))
    except:
        print("Invalid year input.")
        return

    results = run_analysis(
        grade_file="data/grades/cleaned_pub_rec_master.csv",
        degree_file=degree_file,
        start=start,
        end=end,
        recon_map=recon_map
    )
    
        
    for entry in results:
        print(f"\nYear {entry['year']} - Term {entry['term']}")
        print(f"{entry['course']}")

        if entry.get('asterisk_only'):
            print(f"Class {entry['course']} is required but no grade data available.")
        elif entry.get('missing'):
            print("Missing data for this course.")
        elif entry.get('no_data'):
            print("No data available for this course.")
        else:
            print(f"Overall: {entry['distribution']}")

            instructors = entry.get('instructors', {})

            if instructors:
                ranked = rank_instructors(instructors)
                if ranked:
                    top = ranked[0]
                    print(
                        f"Top Instructor: {top['instructor']} | "
                        f"A: {top['A']}% | Pass: {top['Pass']}% | "
                        f"DNF: {top['DNF']}% | N={top['total']}"
                    )
                else:
                    print("No instructor data available.")
            else:
                print("No instructor data available.")

if __name__ == "__main__":
    main()