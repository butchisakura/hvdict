# Update Content
+ add/update files *.md in "src" directory
+ content follow markdown format
+ copy template from another

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