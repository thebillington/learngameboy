#!/usr/bin/env python3
import os
import re
import shutil

import yaml
from jinja2 import Environment, FileSystemLoader

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
OUTPUT_DIR = os.path.join(BASE_DIR, 'docs')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
IMAGES_DIR = os.path.join(BASE_DIR, 'images')

N_ARTIFACT_RE = re.compile(r'>\s*n\s*<')
IMG_RE = re.compile(r'(src=["\'])(/images/|https?://learngameboy\.com/images/)')
LINK_RE = re.compile(r'href=["\']https?://learngameboy\.com/([^"\']*)["\']')


def load_yaml(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return yaml.safe_load(f)


def clean_n_artifacts(html):
    if not html:
        return html
    return N_ARTIFACT_RE.sub('>\n<', html)


def fix_content_paths(html, root_path):
    if not html:
        return html
    html = IMG_RE.sub(r'\1' + root_path + 'images/', html)
    html = LINK_RE.sub(lambda m: 'href="' + root_path + m.group(1).rstrip('/') + '/index.html"', html)
    return html


def build_page_tree(pages):
    by_id = {p['id']: p for p in pages}

    for p in pages:
        p['children'] = []
        p['parent_slug'] = None

    for p in pages:
        parent_id = p.get('parent', 0)
        if parent_id != 0 and parent_id in by_id:
            parent = by_id[parent_id]
            parent['children'].append(p)
            p['parent_slug'] = parent['slug']

    for p in pages:
        p['children'].sort(key=lambda x: x.get('menu_order', 0))

    page_map = {p['slug']: p for p in pages}

    top_pages = [p for p in pages if p.get('parent', 0) == 0 and p.get('show_in_menu')]
    top_pages.sort(key=lambda p: p.get('menu_order', 0))

    return top_pages, page_map, by_id


def render_page(template, context, output_path):
    html = template.render(**context)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(html)


def main():
    site = load_yaml('site.yml')
    pages = load_yaml('pages.yml')

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

    top_pages, page_map, by_id = build_page_tree(pages)

    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

    shutil.copytree(ASSETS_DIR, os.path.join(OUTPUT_DIR, 'assets'))
    shutil.copytree(IMAGES_DIR, os.path.join(OUTPUT_DIR, 'images'))

    home_id = site.get('home_page', 2)

    for page in pages:
        page['html'] = clean_n_artifacts(page.get('html', ''))

    base_context = {
        'site': site,
        'top_pages': top_pages,
        'page_map': page_map,
        'home_id': home_id,
    }

    for page in pages:
        slug = page['slug']
        root_path = '' if page['id'] == home_id else '../'
        html = fix_content_paths(page.get('html', ''), root_path)
        context = dict(base_context, page_title=page['title'], page_slug=slug, page=page, root_path=root_path)
        context['page'] = dict(page, html=html)

        if page['id'] == home_id:
            template = env.get_template('index.html')
            render_page(template, context, os.path.join(OUTPUT_DIR, 'index.html'))
        else:
            template = env.get_template('page.html')
            render_page(template, context, os.path.join(OUTPUT_DIR, slug, 'index.html'))

    print('Site generated successfully!')


if __name__ == '__main__':
    main()
