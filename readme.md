https://www.mkdocs.org/getting-started/

# install
pip install mkdocs

# Update Content
+ add/update files *.md in "src" directory
+ include image by relative path from current document (md)
+ content follow markdown format
+ copy template from another

# mkdocs.yml
site_build_version: update version when deploy new version

docs_dir: src => our source md files
site_dir: docs => output source

theme:
  name: null
  custom_dir: 'hvdict_theme/'  => directory contain static file (js, css, images)
  include_search_page: true
  search_index_only: false
  static_templates:
    - 404.html

Customize in theme directory
+ robots.txt
+ base.html (base template)
+ {{base_url}} will allow add absolute or base url to avoid wrong resolve path

# Link media
https://www.mkdocs.org/user-guide/writing-your-docs/#linking-to-images-and-media

Method 1: put image into hvdict_theme/img
Method 2: put imgae into src/img

Reference image by relative path

# Publish
+ update site build version: mkdocs.yml > site_build_version
+ rebuild docs: mkdocs build
+ update master: via git (add, commit, push)
+ update release: via git (merge master, push)
+ test local: mkdocs serve (stop = ctrl C)

+ finally, update git: 
  + git add .
  + git commit -m "update"
  + git push