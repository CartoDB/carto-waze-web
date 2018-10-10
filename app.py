import io
import os
from random import choice
from string import ascii_letters
import psycopg2
from flask import Flask, render_template, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, DateTimeField
from wtforms.validators import DataRequired
from flask_wtf.csrf import CSRFProtect
from cartowaze.backends.waze_ccp_processor import AlertProcessor, JamProcessor
from carto.auth import APIKeyAuthClient
from carto.exceptions import CartoException


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_me")

csrf = CSRFProtect(app)


def get_table_name():
    table_name = "waze_{random_part}".format(random_part="".join(choice(ascii_letters) for i in range(12)))
    return table_name


class MainForm(FlaskForm):
    incident_type = SelectField(choices=[("alerts", "Alerts"), ("jams", "Jams")])
    db_host = StringField("DB host", default="development-tf-waze-data-aurora-cluster.<cluster id>.<region>.rds.amazonaws.com", validators=[DataRequired()])
    db_username = StringField("DB user name", default="waze_readonly", validators=[DataRequired()])
    db_password = PasswordField("DB password", validators=[DataRequired()])
    carto_base_url = StringField("API base URL", default="https://<your CARTO username>.carto.com", validators=[DataRequired()])
    carto_api_key = StringField("API key", validators=[DataRequired()])
    carto_table_name = StringField("Destination table name", render_kw={"placeholder": "Leave blank to autogenerate one"})
    from_timestamp = DateTimeField("Start time", validators=[DataRequired()], format="%Y-%m-%d %H:%M")
    to_timestamp = DateTimeField("End time", validators=[DataRequired()], format="%Y-%m-%d %H:%M")


@app.route("/", methods=('GET', 'POST'))
def index():
    form = MainForm()

    if form.validate_on_submit():
        auth_client = APIKeyAuthClient(form.carto_base_url.data, form.carto_api_key.data)

        if form.incident_type.data == "alerts":
            incidents = AlertProcessor(auth_client, username=form.db_username.data, password=form.db_password.data, host=form.db_host.data)
        elif form.incident_type.data == "jams":
            incidents = JamProcessor(auth_client, username=form.db_username.data, password=form.db_password.data, host=form.db_host.data)
        else:
            flash("Unknown incident type: {incident_type}".format(incident_type=form.incident_type.data), "error")
            return render_template("index.html", form=form)

        with io.StringIO() as csv_out:
            try:
                incidents.get_values(csv_out, pub_utc_date__gt=form.from_timestamp.data, pub_utc_date__lt=form.to_timestamp.data)
            except psycopg2.OperationalError as e:
                form.db_host.errors = True
                flash(e, "error")
                return render_template("index.html", form=form)
            else:
                csv_out.seek(0)

            with io.BytesIO(bytes(csv_out.read(), "utf-8")) as csv_in:
                table_name = form.carto_table_name.data or get_table_name()
                try:
                    incidents.create_table(table_name=table_name, cartodbfy=True)
                except CartoException as e:
                    form.carto_base_url.errors = True
                    flash(e, "error")
                    return render_template("index.html", form=form)

                try:
                    incidents.append_data(csv_in, table_name=table_name)
                except CartoException as e:
                    flash(e, "error")
                    return render_template("index.html", form=form)

                flash("Data has been saved in CARTO ({table_name})".format(table_name=table_name), "success")
    else:
        flash(form.errors, "error")

    return render_template("index.html", form=form)
