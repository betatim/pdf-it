# Create PDFs!


## Deploying

A demo of this is hosted on Heroku at https://pdf-it.herokuapp.com

Deploy it your favourite way: auto-deploy via GitHub integration or manually
with a remote like `ssh://git@heroku.com/pdf-it.git` called `heroku` and then
running `git push heroku master:master`

We use the libreoffice buildpack for heroku: https://github.com/BlueTeaLondon/heroku-buildpack-libreoffice-for-heroku-18. If you setup a new heroku instance follow the instructions
for adding the buildpack.

## Local development

Install Python 3.9, install libreoffice (`soffice` has to be on your PATH),
`pip install -e .`, run `pdfitapp --debug --port=8080`, and visit
http://localhost:8080/.
