#!/usr/bin/env python3
"""Add a book to books.json and fetch its cover.

  python3 add-book.py \
      --title "East of Eden" \
      --author "John Steinbeck" \
      --rating 4.75 \
      --finished 05/12/2026 \
      --cover "https://i.gr-assets.com/.../28251243._SY475_.jpg" \
      --review "https://www.goodreads.com/review/show/7836298716" \
      --author-link "https://www.goodreads.com/author/show/585.John_Steinbeck"

--cover takes a URL or a local file path. Covers are stored at 96px wide WebP
in assets/covers/. --rating is 0 to 5 in quarter stars, as on Goodreads.
--finished accepts MM/DD/YYYY or MM/YYYY. Only --title,
--author, --rating and --finished are required; the page sorts and groups by
date on its own, so order in the file does not matter.
"""
import argparse, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))

def slug(t):
    return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')[:60]

def quarter_stars(v):
    try:
        n = float(v)
    except ValueError:
        raise argparse.ArgumentTypeError(f'not a number: {v!r}')
    if not 0 <= n <= 5 or n * 4 % 1:
        raise argparse.ArgumentTypeError(f'must be 0 to 5 in steps of 0.25, got {v}')
    return int(n) if n.is_integer() else n

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--title', required=True)
    p.add_argument('--author', required=True)
    p.add_argument('--rating', required=True, type=quarter_stars,
                   help='0 to 5 in steps of 0.25')
    p.add_argument('--finished', required=True, help='MM/DD/YYYY or MM/YYYY')
    p.add_argument('--cover', help='image URL or local file')
    p.add_argument('--review', default='')
    p.add_argument('--author-link', dest='author_link', default='')
    a = p.parse_args()

    if not re.fullmatch(r'\d{1,2}/(\d{1,2}/)?\d{4}', a.finished):
        sys.exit(f'--finished must be MM/DD/YYYY or MM/YYYY, got {a.finished!r}')

    books = json.load(open(os.path.join(ROOT, 'books.json')))
    if any(b['title'].lower() == a.title.lower() for b in books):
        sys.exit(f'{a.title!r} is already in books.json')

    s = slug(a.title)
    rel = f'assets/covers/{s}.webp'
    out = os.path.join(ROOT, rel)

    if a.cover:
        tmp = os.path.join(ROOT, '.cover-tmp')
        if a.cover.startswith('http'):
            # Goodreads serves a small default; ask for a larger source so the
            # 96px target is a downscale. curl, because python's SSL trust
            # store is not set up on this machine.
            url = re.sub(r'_S[XY]\d+_', '_SY475_', a.cover)
            for u in (url, a.cover):
                r = subprocess.run(['curl', '-sSL', '--max-time', '25',
                                    '-A', 'Mozilla/5.0', '-o', tmp, u])
                if r.returncode == 0 and os.path.getsize(tmp) > 500:
                    break
            else:
                sys.exit('could not download the cover')
        else:
            subprocess.run(['cp', os.path.expanduser(a.cover), tmp], check=True)
        subprocess.run(['cwebp', '-quiet', '-q', '82', '-resize', '96', '0',
                        tmp, '-o', out], check=True)
        os.remove(tmp)
        print(f'cover  -> {rel} ({os.path.getsize(out) // 1024} KB)')
    elif not os.path.exists(out):
        print(f'no --cover given; the page will hide the empty slot until '
              f'{rel} exists')

    books.append({
        'title': a.title,
        'cover': rel,
        'review': a.review,
        'author': a.author,
        'authorLink': a.author_link,
        'rating': a.rating,
        'finished': a.finished,
    })
    with open(os.path.join(ROOT, 'books.json'), 'w') as f:
        json.dump(books, f, indent=2, ensure_ascii=False)
    print(f'added  -> {a.title} ({len(books)} books)')

if __name__ == '__main__':
    main()
