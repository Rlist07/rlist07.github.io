#!/usr/bin/env python3
"""Build the site: compile CSS, then stamp it and the nav rail into every page.

    python3 build.py

Everything the browser needs is inlined, so a page paints correctly from the
first byte with no extra requests and no nav flash. Edit sidebar.html to change
the nav, then run this. The pre-commit hook runs it for you.
"""
import glob, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

# Each section's own pages, in the order its index lists them. Labels are
# shortened where the page title will not fit the 176px rail.
CHILDREN = {
    'projects.html': [
        ('beerbelly.html',   'Beerbelly'),
        ('bevboost.html',    'BevBoost'),
        ('h4d.html',         '3D models'),
        ('balloons.html',    'Balloons'),
        ('website.html',     'This website'),
    ],
    'hobbies.html': [
        ('shed.html',        'Shed'),
        ('woodworking.html', 'Woodworking'),
        ('reading.html',     'Reading'),
        ('hifi.html',        'HiFi'),
        ('music.html',       'Music'),
    ],
}
SECTION = {c: parent for parent, kids in CHILDREN.items() for c, _ in kids}

SUB_CLASS = ('mt-1 flex w-full basis-full flex-col gap-y-1 pl-3 '
             'md:w-auto md:basis-auto')


def compile_css():
    css = os.path.join(ROOT, '.build.css')
    r = subprocess.run([os.path.join(ROOT, 'node_modules/.bin/tailwindcss'),
                        '-i', 'input.css', '-o', css, '--minify'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit('tailwind failed:\n' + r.stderr)
    out = open(css).read().strip()
    os.remove(css)
    return out


def rail_for(page, template):
    """The shared rail, with this page's current-marker and sub-menu applied."""
    here = page.lower()
    section = SECTION.get(here)
    open_section = section or (here if here in CHILDREN else None)
    html = template

    def mark(m):
        attrs, label = m.group(1), m.group(2)
        href = re.search(r'href="([^"]*)"', attrs).group(1).lower()
        cls = re.search(r'class="([^"]*)"', attrs).group(1)
        if href == here:
            # A self-link goes nowhere; a span is the correct element.
            return f'<span class="{cls.replace("text-muted", "text-ink")}" aria-current="page">{label}</span>'
        if href == section:
            # Marked, but it MUST stay a link or a child page has no way back.
            return (f'<a {attrs.replace(cls, cls.replace("text-muted", "text-ink"))} '
                    f'aria-current="location">{label}</a>')
        return m.group(0)

    # Scope to the <nav> only. The wordmark above it also points at index.html,
    # and marking it would turn the name into a non-link with a tick beside it.
    nav_m = re.search(r'<nav\b.*?</nav>', html, re.S)
    nav = re.sub(r'<a ([^>]*?)>([^<]*)</a>', mark, nav_m.group(0))
    html = html[:nav_m.start()] + nav + html[nav_m.end():]

    if open_section:
        rows = []
        for href, label in CHILDREN[open_section]:
            if href == here:
                rows.append(f'      <span class="text-ink no-underline" aria-current="page">{label}</span>')
            else:
                rows.append(f'      <a href="{href}" class="text-muted no-underline '
                            f'hover:text-ink hover:underline">{label}</a>')
        sub = f'\n    <span class="{SUB_CLASS}">\n' + '\n'.join(rows) + '\n    </span>'
        # Insert directly after the section's own nav item.
        html = re.sub(r'(<(?:a|span)[^>]*?(?:href="' + re.escape(open_section) +
                      r'"|aria-current="page")[^>]*>[^<]*</(?:a|span)>)',
                      lambda m: m.group(1) + sub, html, count=1)
    return html


def main():
    css = compile_css()
    template = open('sidebar.html').read().strip()
    pages = [f for f in sorted(glob.glob('*.html')) if f != 'sidebar.html']
    changed = 0
    for f in pages:
        s = open(f).read(); o = s
        s = re.sub(r'<!-- css:start -->.*?<!-- css:end -->',
                   lambda _: f'<!-- css:start --><style>{css}</style><!-- css:end -->',
                   s, flags=re.S)
        rail = rail_for(f, template)
        s = re.sub(r'<!-- rail:start -->.*?<!-- rail:end -->',
                   lambda _: f'<!-- rail:start -->\n    {rail}\n      <!-- rail:end -->',
                   s, flags=re.S)
        if s != o:
            open(f, 'w').write(s); changed += 1
    print(f'built: {len(css) // 1024}KB css + rail stamped into {len(pages)} pages '
          f'({changed} changed)')


if __name__ == '__main__':
    main()
