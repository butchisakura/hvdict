# Update Content
+ create/update file in "src" directory
+ file extension *.md
+ content follow markdown format

# Publish
+ update site build version: mkdocs.yml > site_build_version
+ rebuild docs: mkdocs build
+ update master: via git (add, commit, push)
+ update release: via git (merge master, push)
+ test local: mkdocs serve (stop = ctrl C)