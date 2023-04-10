from flask import Flask, flash, render_template, redirect, url_for, request, session
from datetime import timedelta
import requests
from string import Template
from datetime import datetime
import os
import psycopg2
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from forms import PostIssueForm, ProjectNameForm

jira_url = ""

# DATABASE_URL = "postgresql://postgres:SuperSecret@localhost:5432/content"
# url = os.environ.get("DATABASE_URL")
# connection = psycopg2.connect(host="localhost",database="content", user="postgres",password="SuperSecret")

# CREATE_TYPE_TABLE = (
#     "CREATE TABLE IF NOT EXISTS {type} (id SERIAL PRIMARY KEY, title TEXT, status INTEGER, maxstatus INTEGER, tag TEXT, info TEXT, completed BOOLEAN)"

# )

# INSERT_INTO_TABLE = (
#     "INSERT INTO {type} (title, status, maxstatus, completed, info, tag) VALUES('{title}', '{status}', '{maxstatus}', '{completed}', '{info}', '{tag}')"
# )


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:SuperSecret@localhost:5432/projectTracker"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '2313'
db = SQLAlchemy(app)


class Projects(db.Model):
    # attributes for project
    name = db.Column(db.String(100), primary_key = True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    last_updated = db.Column(db.DateTime, server_default=func.now())
    outstanding_issues = db.Column(db.Integer, nullable=False)

    def to_json(self):
        return {
            "name": self.name,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "outstanding_issues": self.outstanding_issues
        }
    
class Issues(db.Model):
    # attributes for issues table
    id = db.Column(db.Integer, primary_key = True)
    project = db.Column(db.String(100))
    subject = db.Column(db.String(100))
    description = db.Column(db.String)
    created_at = db.Column(db.DateTime, server_default=func.now())
    last_updated = db.Column(db.DateTime, server_default=func.now())

    def to_json(self):
        return {
            "id": self.id,
            "project": self.project,
            "subject": self.subject,
            "description": self.description,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
        }

with app.app_context():    
    db.create_all()

@app.route("/")
def home():
    projects = Projects.query
    return render_template("index.html", title="Current Projects", projects=projects)



# @app.post("/project/new_project")
# def create_new_project():
#     data = request.get_json()
#     name = data["name"]
#     with connection:
#         with connection.cursor() as cursor:
#             cursor.execute(INSERT_INTO_TABLE.format(name=name))
#     return {"name": name, "message": f"Project {name} created."}, 201


# @app.post("/project/create_table")
# def create_new_project_type():
#     data = request.get_json()
#     type = data["type"]
#     with connection:
#         with connection.cursor() as cursor:
#             cursor.execute(CREATE_TYPE_TABLE.format(type=type))
#     return {"type": type, "message": f"Type {type} created."}, 201


@app.route("/project/<string:projectName>", methods=["GET", "POST"])
def get_project_page(projectName=""):
    project=Projects.query.get_or_404(projectName)
    # if request.method == "POST":
    #     # on project name click 
    #     print(projectName)
    #     # return the project page
    #     # current bugs + options to add new bugs/issues
    
    if "newIssue" in request.form:
        db.session.add(Issues(project=projectName, created_at=None, last_updated=None, subject="", description=""))
        
        project.outstanding_issues += 1
        project.last_updated=func.now()
        db.session.commit()
        return redirect(request.referrer)

    elif "delete" in request.form:
        issue_id = request.form["delete"]
        project.last_updated=func.now()
        delete_issue(issue_id, projectName)
    issues = Issues.query.filter_by(project=projectName).all()

    return render_template("project.html", title=projectName, issues=issues, project=projectName)

# @app.route("/project/<string:projectName>/projectMain", methods = ["GET", "POST"])
# def projectMain(projectName):
   
#     if request.method == "POST":

#         print(request.form)
#         print(projectName)
    
    
#     return redirect(request.referrer)

@app.route("/project/<string:projectName>/<int:issue_id>", methods=["GET", "POST"])
def issue(issue_id, projectName):
    issue = Issues.query.get_or_404(issue_id)
    return render_template("issue.html", title="Issue", issue=issue, projectName=projectName)


@app.route("/project/<string:projectName>/<int:issue_id>/update",methods=['GET' ,'Post'])
def update_issue(issue_id, projectName):
    issue=Issues.query.get_or_404(issue_id)
  
    form=PostIssueForm()
    if request.method=='POST':
        issue.subject=form.Subject.data
        issue.description=form.Description.data
        project=Projects.query.get_or_404(projectName)
        project.last_updated = func.now()
        issue.last_updated=func.now()
        db.session.commit()
        flash('Issue updated! ', 'success')
        return render_template("issue.html", title="Issue", issue=issue, projectName=projectName)
 
    elif request.method == 'GET':
        form.Subject.data = issue.subject
        form.Description.data = issue.description
   
    return render_template('issue_update.html',title=issue.subject,issue=issue,form=form, issue_id=issue_id)

@app.route("/project/<string:projectName>/<int:issue_id>/delete", methods=['GET','POST'])
def delete_issue(issue_id, projectName):
    issue = Issues.query.get_or_404(issue_id)
    db.session.delete(issue)
    project=Projects.query.get_or_404(projectName)
    project.outstanding_issues -= 1
    project.last_updated = func.now()
    db.session.commit()
    flash('Your issue has been deleted!', 'success')
    return redirect(url_for('get_project_page', projectName=projectName))

# @app.route("/project/rename/<string:projectName>", methods=["GET", "POST", "DELETE"])
# def rename_project(projectName):

#     print(projectName)
#     form = ProjectNameForm()
#     project=Projects.query.get_or_404(projectName)
#     print("here3")
#     project.name=form.Name.data
    
#     print("rename")
#     db.session.commit()
#     home()

@app.route("/project", methods=["GET", "POST", "DELETE"])
def project(projectName=""):
    if request.method == "POST":
        if "newProject" in request.form:
            #projectName += "create new project"
            # get total number of projects in table
            # create a new project with name project(x) where x
            # is total number of projects + 1
            rowCount = Projects.query.count()
            projectName += "Project " + str(rowCount + 1)
            dupeCount = 1
            while Projects.query.filter_by(name=projectName).first():
                projectName = "Project" + str(rowCount + dupeCount)
                dupeCount += 1
            db.session.add(Projects(name=projectName, created_at=func.now(), last_updated=func.now(), outstanding_issues=0))
            db.session.commit()

        elif "delete" in request.form:
            projectName = request.form["delete"]
            del_obj = Projects.query.filter_by(name=projectName).one()
            db.session.delete(del_obj)
            db.session.commit()

        elif "rename" in request.form:
            projectName = request.form["rename"]
            project=Projects.query.get_or_404(projectName)
            form = ProjectNameForm()
            form.Name.data = project.name
            print(project.name)
            return render_template('project_update.html',projectName=project.name,form=form)
        
        else:
            form = ProjectNameForm()
            projectName = request.form["post"]
            project=Projects.query.get_or_404(projectName)
            project.name=form.Name.data
            project.last_updated=func.now()
            issues = Issues.query.filter_by(project=projectName).all()
            for issue in issues:
                issue.project = form.Name.data
            db.session.commit()
            flash('Project Name updated! ', 'success')
            projects = Projects.query
            return render_template("index.html", title="Current Projects", projects=projects)
        
    # return {"name": projectName}, 201

    return redirect(request.referrer)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')


