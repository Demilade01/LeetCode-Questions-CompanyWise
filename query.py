#!/usr/bin/env python3
"""
LeetCode Company-Wise Query Tool
A zero-dependency CLI tool to search, filter, and inspect company-specific
interview questions across 200 tech companies and 4 timeframe windows.
"""

import os
import csv
import argparse
import sys


def find_company_dirs(base_path):
    dirs = []
    for entry in sorted(os.listdir(base_path)):
        full_path = os.path.join(base_path, entry)
        if os.path.isdir(full_path) and not entry.startswith('.'):
            # Check if directory contains timeframe CSVs
            csv_files = [f for f in os.listdir(full_path) if f.endswith('.csv')]
            if csv_files:
                dirs.append(entry)
    return dirs


def load_questions(base_path, company=None, timeframe=None, difficulty=None, query=None, min_freq=0.0):
    all_companies = find_company_dirs(base_path)
    
    selected_companies = []
    if company:
        comp_query = company.strip().lower()
        # Exact match first, then substring match
        exact = [c for c in all_companies if c.lower() == comp_query]
        if exact:
            selected_companies = exact
        else:
            selected_companies = [c for c in all_companies if comp_query in c.lower()]
            if not selected_companies:
                print(f"[!] No company directory found matching '{company}'.", file=sys.stderr)
                print(f"    Available companies: {len(all_companies)} total.", file=sys.stderr)
                return []
    else:
        selected_companies = all_companies

    results = []
    allowed_timeframes = None
    if timeframe:
        tf_name = timeframe.lower()
        if not tf_name.endswith('.csv'):
            tf_name += '.csv'
        allowed_timeframes = {tf_name}

    for comp in selected_companies:
        comp_dir = os.path.join(base_path, comp)
        for fname in os.listdir(comp_dir):
            if not fname.endswith('.csv'):
                continue
            if allowed_timeframes and fname not in allowed_timeframes:
                continue

            tf_label = fname.replace('.csv', '')
            fpath = os.path.join(comp_dir, fname)

            with open(fpath, mode='r', encoding='utf-8', errors='ignore') as fp:
                reader = csv.reader(fp)
                try:
                    headers = next(reader)
                except StopIteration:
                    continue

                for row in reader:
                    if len(row) < 6:
                        continue
                    qid, title, acceptance, diff, freq_str, link = (
                        row[0].strip(),
                        row[1].strip(),
                        row[2].strip(),
                        row[3].strip(),
                        row[4].strip(),
                        row[5].strip(),
                    )

                    # Difficulty filter
                    if difficulty and diff.lower() != difficulty.strip().lower():
                        continue

                    # Query keyword filter
                    if query and query.strip().lower() not in title.lower():
                        continue

                    # Frequency filter
                    try:
                        freq_val = float(freq_str)
                    except ValueError:
                        freq_val = 0.0

                    if freq_val < min_freq:
                        continue

                    results.append({
                        'company': comp,
                        'timeframe': tf_label,
                        'id': qid,
                        'title': title,
                        'difficulty': diff,
                        'acceptance': acceptance,
                        'frequency': freq_val,
                        'link': link,
                    })

    # Sort results by frequency descending by default
    results.sort(key=lambda x: x['frequency'], reverse=True)
    return results


def print_table(results, limit=None):
    if not results:
        print("No matching questions found.")
        return

    display_set = results[:limit] if limit else results
    headers = ["Company", "Window", "ID", "Difficulty", "Acceptance", "Frequency", "Title"]

    # Calculate column widths
    c_w = max(len(headers[0]), max(len(r['company']) for r in display_set))
    w_w = max(len(headers[1]), max(len(r['timeframe']) for r in display_set))
    i_w = max(len(headers[2]), max(len(r['id']) for r in display_set))
    d_w = max(len(headers[3]), max(len(r['difficulty']) for r in display_set))
    a_w = max(len(headers[4]), max(len(r['acceptance']) for r in display_set))
    f_w = 9
    t_w = max(len(headers[6]), min(50, max(len(r['title']) for r in display_set)))

    row_fmt = f"{{:<{c_w}}} | {{:<{w_w}}} | {{:<{i_w}}} | {{:<{d_w}}} | {{:<{a_w}}} | {{:<{f_w}}} | {{:<{t_w}}}"
    sep = "-" * (c_w + w_w + i_w + d_w + a_w + f_w + t_w + 18)

    print()
    print(row_fmt.format(*headers))
    print(sep)
    for r in display_set:
        title_disp = r['title'] if len(r['title']) <= t_w else r['title'][:t_w - 3] + "..."
        freq_disp = f"{r['frequency']:.3f}"
        print(row_fmt.format(
            r['company'],
            r['timeframe'],
            r['id'],
            r['difficulty'],
            r['acceptance'],
            freq_disp,
            title_disp
        ))
    print(sep)
    print(f"Total matching results: {len(results)}" + (f" (showing top {limit})" if limit and limit < len(results) else ""))
    print()


def export_csv(results, output_path):
    with open(output_path, mode='w', newline='', encoding='utf-8') as fp:
        writer = csv.writer(fp)
        writer.writerow(["Company", "Timeframe", "ID", "Title", "Difficulty", "Acceptance", "Frequency", "Link"])
        for r in results:
            writer.writerow([
                r['company'],
                r['timeframe'],
                r['id'],
                r['title'],
                r['difficulty'],
                r['acceptance'],
                f"{r['frequency']:.4f}",
                r['link']
            ])
    print(f"[✓] Successfully exported {len(results)} rows to '{output_path}'.")


def main():
    parser = argparse.ArgumentParser(
        description="Search, filter, and inspect company-wise LeetCode interview questions."
    )
    parser.add_argument("-c", "--company", help="Target company name or substring (e.g. google, amazon, citadel)")
    parser.add_argument("-t", "--timeframe", choices=["6months", "1year", "2year", "alltime"], help="Time window")
    parser.add_argument("-d", "--difficulty", choices=["Easy", "Medium", "Hard", "easy", "medium", "hard"], help="Filter by difficulty tier")
    parser.add_argument("-q", "--query", help="Keyword search in problem title (e.g. 'island', 'tree', 'lru')")
    parser.add_argument("--min-freq", type=float, default=0.0, help="Minimum frequency threshold (default: 0.0)")
    parser.add_argument("-n", "--top", type=int, help="Limit output to top N results")
    parser.add_argument("-o", "--output", help="Export filtered results to a CSV file")
    parser.add_argument("--list-companies", action="store_true", help="List all 200 available companies and exit")

    args = parser.parse_args()
    base_dir = os.path.dirname(os.path.abspath(__file__))

    if args.list_companies:
        companies = find_company_dirs(base_dir)
        print(f"\nAvailable companies ({len(companies)} total):")
        for i, comp in enumerate(companies, 1):
            print(f"{i:3d}. {comp}")
        print()
        return

    results = load_questions(
        base_path=base_dir,
        company=args.company,
        timeframe=args.timeframe,
        difficulty=args.difficulty,
        query=args.query,
        min_freq=args.min_freq
    )

    if args.output:
        export_csv(results, args.output)
    else:
        print_table(results, limit=args.top)


if __name__ == "__main__":
    main()
