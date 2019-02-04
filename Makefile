
gh-pages:
	git checkout gh-pages
	rm .git/index || true
	git clean -fdx
	git checkout master doc/Makefile doc/source api/src pom.xml
	git reset HEAD
	cd doc; make html
	cp -rfv doc/build/html/. ./
	rm -rf doc api pom.xml
	git add -A && git commit -m "Generated gh-pages for `git log master -1 --pretty=short --abbrev-commit`" && git push origin gh-pages ; git checkout master

