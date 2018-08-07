# paperwiki


Paperwiki is a platform to foster open discussions about academic papers.

Architecture:
Uses google scholar to search for articles (use scholar.py)
"Create Page" will generate a DB for an article
that would be saved into mongodb.
A page will have the following format.
Title.
Authors & Affiliations.
Year. Journal. Page. Etc.

Abstract

Paperwiki section
[People can enter information about the article]

# Features
- search google scholar
- create or see wiki pages on each paper
- each wiki page will also host a reddit-like forum for discussions
- main page will have a feed for recent wiki updates
- users who contribute to the wiki will be notified when changed
- users can star (bookmark) papers to their paperwiki library.
- network map of literature. 

# Resources
https://github.com/reddit-archive/reddit
https://github.com/ckreibich/scholar.py
https://flaskbb.readthedocs.io/en/latest/installation.html
