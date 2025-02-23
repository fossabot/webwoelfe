import sentry_sdk
from sentry_sdk import last_event_id
from sentry_sdk.integrations.flask import FlaskIntegration
from shutil import ExecError
from flask_api import status
from traceback import print_tb  # skipcq: PY-W2000
from flask import (  # skipcq: PY-W2000
    Flask,
    request,
    url_for,
    render_template,
    session,
    make_response,
    redirect,
    Response,
    escape,
)
import jsonify


import werwolf
import datetime
import re
from inspect import currentframe, getframeinfo
from datetime import datetime


sentry_sdk.init(
    dsn="https://78fe9de58a5847ada071bf5f62f9c214@o1363527.ingest.sentry.io/6678492",
    integrations=[
        FlaskIntegration(),
    ],
    traces_sample_rate=0.5,
)


app = Flask(__name__)

# index page


@app.route("/", methods=["GET"])  # Homepage
def index():
    """
    The index function is the main page of the application. It is called when a user navigates to
    the root directory of our web application. The function returns an HTML template that contains
    a list of links to other pages within our web application.

    :return: The index page of the application.

    """
    werwolf.in_log_schreiben("index geöffnet")
    return render_template(
        "index.html", spieler_suche=bool(werwolf.suche_spieler())
    )  # Render index.html


# einstellungen


@app.route("/einstellungen", methods=["GET"])  # Einstellungen
def einstellungen():
    """
    The einstellungen function is used to open the einstellungen page.


    :return: The einstellungen

    """
    werwolf.in_log_schreiben("einstellungen geöffnet")
    return render_template("einstellungen.html")  # Render einstellungen.html


# wie viele Spieler sollen vorhanden sein?

# Spieleranzahl
@app.route("/einstellungen/spieleranzahl", methods=["POST"])
def setPlayerNumber():  # set the number of players
    """
    The setPlayerNumber function is called when the user clicks on the button &quot;Spieleranzahl setzen&quot; in einstellungen.html.
    It takes a number of players from the form and checks if it is an integer between 8 and 18, otherwise it sets it to 8.
    If the checkbox &quot;Erzähler ist zufällig&quot; is checked, erzaehler_flag = 1 else 0.

    :return: The number of players

    """
    # get the number of players from the form
    spieleranzahl = request.form.get("num")
    try:
        # eingabe ist wirklich ein integer
        spieleranzahl_int = int(spieleranzahl)
        if (
            spieleranzahl_int < 8 or spieleranzahl_int > 18
        ):  # Spieleranzahl ist zwischen 8 und 18
            spieleranzahl = 8  # auf 8 defaulten
    except ValueError:
        spieleranzahl = 8  # auf 8 defaulten

    # speichern der spieleranzahl in einer textdatei
    with open("spieler_anzahl.txt", "w+") as file:
        file.write(str(spieleranzahl))
    if bool(request.form.get("cbx")) is True:  # checkbox is checked
        erzaehler_flag = 1  # set erzaehler_flag to 1
    else:
        erzaehler_flag = 0  # set erzaehler_flag to 0
    # speichern des erzaehler_flag in einer textdatei
    with open("erzaehler_ist_zufaellig.txt", "w+") as flag:
        # speichern des erzaehler_flag in einer textdatei
        flag.write(str(erzaehler_flag))
    werwolf.createDict()  # create the dictionary with the names of the players
    with open("rollen_log.txt", "w+") as f:  # leere rollen_log.txt
        f.write("*********************\n")
    werwolf.in_log_schreiben("Spieleranzahl: auf " + str(spieleranzahl) + " gesetzt")
    # render einstellungen_gespeichert.html
    return render_template(
        "einstellungen_gespeichert.html", spieleranzahl_var=spieleranzahl
    )


# namenseingabe spieler


@app.route("/spieler", methods=["POST"])  # Spieler
def get_data():  # get the data from the form
    """
    The get_data function gets the data from the form. If it is a POST request,
    it gets the name from the form and checks if it is already in use. If so,
    it renders an error page with a link to go back to index.html.

    :return: The name and the operator from the form

    """
    if request.method == "POST":  # if the request is a POST request
        name = request.form.get("name")  # get the name from the form
        name = werwolf.name_richtig_schreiben(name)  # clean the name

        with open("rollen_log.txt") as players_log:  # open the log file
            players_log = players_log.read()  # read the log file
        if werwolf.validiere_name(name) is True:
            # if the name is already in the log file
            # name doppelt ausgeben
            return render_template("name_doppelt.html", name=name)

        with open("spieler_anzahl.txt") as file:
            num = file.read()  # read the file
        operator = werwolf.deduct()  # get the operator
        try:  # try to get the operator
            if operator == 0:  # if the operator is 0
                code = "code"  # set the code to code
                # render spiel_beginnt.html
                return render_template("spiel_beginnt.html", code=code)
            # append the name to the log file
            with open("rollen_log.txt", "a") as names:
                # write the name and the operator to the log file
                names.write(f"{name} = {operator}")
                # names.write(f'{date}: {name} = {operator}')
                # write a new line to the log file
                names.write("\n")
                names.close()
            # append the name to the log file
            with open("rollen_original.txt", "a") as names:
                # write the name and the operator to the log file
                names.write(f"{name} = {operator}")
                # names.write(f'{date}: {name} = {operator}')
                # write a new line to the log file
                names.write("\n")
                # credits to @joschicraft

            token = werwolf.generiere_token(name, operator)
            werwolf.in_log_schreiben(f"Neuer Spieler {name} hat die Rolle {operator}")
            # render rollen_zuweisung.html
            return render_template(
                "rollen_zuweisung.html",
                players=num,
                name=name,
                operator=operator,
                token=token,
            )
        except Exception as e:
            # render neu_laden.html
            return render_template("neu_laden.html")

    else:
        return render_template("fehler.html"), 500


# Pfad des Erzählers, momentan für debugzwecke auf einem ungeschützten pfad


@app.route("/erzaehler", methods=["GET"])  # Erzähler
def erzaehler():
    """
    The erzaehler function opens the log file and renders it to erzaehler.html

    :return: The erzaehler

    """
    try:
        with open("rollen_log.txt") as players_log:  # open the log file
            players_log = players_log.readlines()  # read the log file
        # render erzaehler.html
        werwolf.in_log_schreiben("Erzähler geöffnet")
        return render_template("erzaehler.html", names=players_log)
    except Exception as e:
        return str(404)  # return 404 if the file is not found


# Neues Spiel


# reset der rollen_log.txt
@app.route("/erzaehler/reset", methods=["POST"])
def reset():
    """
    The reset function is called when the user presses the reset button. It resets all files and starts a new game.

    :return: The reset

    """
    if (
        request.method == "POST" and request.form["reset_button"] == "Neues Spiel"
    ):  # wenn neues spiel gewuenscht
        werwolf.leere_dateien()  # leere die dateien
        werwolf.in_log_schreiben("Neues Spiel gestartet")
        # zurück zur einstellungen
        return render_template("einstellungen.html")
    return render_template("fehler.html"), 500


@app.route("/<name>/<rolle>/toeten/<name_kill>")  # kill a player
def kill_player(name, rolle, name_kill):
    """
    The kill_player function is called when a player is killed.
    It takes the name of the player who was killed and their role as arguments.
    If the person who was killed is a Werwolf, it will kill them and return
    the template for dead players. If they are not a Werwolf, it will return an error page.

    :param name: Identify the player that is killed
    :param rolle: Determine which role the player has
    :param name_kill: Get the name of the player that is killed
    :return: The html template &quot;dashboards/status/tot

    """
    auswahl = name_kill
    if rolle in ("Hexe", "Jaeger"):
        if (
            rolle == "Hexe"
            and werwolf.hexe_darf_toeten() is True
            and werwolf.validiere_rolle(name, rolle) is True
        ):
            werwolf.toete_spieler(auswahl)
            werwolf.hexe_verbraucht("toeten")
            werwolf.in_log_schreiben(f"Die Hexe ({name}) hat {name_kill} getötet")
            return render_template(
                "Dashboards/Dash_Hexe.html", name=name, rolle=rolle, name_kill=name_kill
            )

        if rolle == "Jaeger":
            if werwolf.jaeger_darf_toeten() is True:
                werwolf.toete_spieler(auswahl)
                werwolf.jaeger_fertig()
                return render_template(
                    "Dashboards/status/tot.html", name=name, todesgrund=""
                )
            return render_template(
                "Dashboards/status/tot.html", name=name, todesgrund=""
            )
        return render_template("fehler.html"), 500
    return render_template("fehler.html"), 500


@app.route("/<name>/Armor_aktion/<player1>/<player2>")  # player auswahl
def armor_player(player1, player2, name):
    """
    The armor_player function is used to protect the player from being killed by the werewolf.
    The function checks if a player is in the game and if he/she has already selected his/her role.
    If both conditions are met, it will allow him/her to select armor as a role.

    :param player1: Store the name of the player who is currently playing
    :param player2: Determine the player who is attacked
    :param name: Determine which player is the armor
    :return: The status of the game

    """
    rolle = "Armor"

    if (
        werwolf.validiere_rolle(name, rolle) is True
        and werwolf.armor_darf_auswaehlen() is True
    ):

        werwolf.armor_fertig(player1, player2)
        return render_template("Dashboards/status/aktion_warten.html")

    if (
        werwolf.armor_darf_auswaehlen() is False
        and werwolf.validiere_rolle(name, rolle) is True
    ):

        return render_template("Dashboards/status/aktion_warten.html")

    if werwolf.validiere_rolle(name, rolle) is False:
        # print the error
        print("Spieler oder Rolle falsch!")
        # render the url_system.html
        return render_template("url_system.html", name=name, rolle=rolle)
    return render_template("fehler.html"), 500


@app.route("/<name>/<rolle>/warten_auf_aktions_ende")
def aktion_warten(name, rolle):
    """
    The aktion_warten function is used to render the template for the aktion_warten page.
    It takes two arguments, name and rolle. If name is in werwolf.rolle and rolle is a valid role,
    then it will return a rendered template of aktion_warten.

    :param name: Identify the player
    :param rolle: Determine the role of the player
    :return: The template for the warten page

    """
    if werwolf.validiere_rolle(name, rolle) is True:
        return render_template("Dashboards/status/aktion_warten.html")
    return render_template("fehler.html"), 500


# Übersicht der Spieler


@app.route("/uebersicht/<ist_unschuldig>")  # Übersicht
def overview_all(ist_unschuldig):  # Übersicht
    """
    The overview_all function renders the overview_innocent.html or overview_guilty.html template, depending on the value of ist_unschuldig.

    :param ist_unschuldig: Distinguish between the innocent and guilty overview
    :return: The overview_innocent

    """
    try:
        # ist_unschuldig ist wirklich ein integer
        ist_unschuldig = int(ist_unschuldig)
        if ist_unschuldig == 1:  # wenn ist_unschuldig = 1
            with open("rollen_original.txt") as players_log:  # open the log file
                players_log = players_log.readlines()  # read the log file
            # render overview_innocent.html
            return render_template("overview_innocent.html", names=players_log)
        if ist_unschuldig == 0:  # wenn ist_unschuldig = 0
            with open("rollen_oriinal.txt") as players_log:  # open the log file
                players_log = players_log.readlines()  # read the log file
            # render overview_guilty.html
            return render_template("overview_guilty.html", names=players_log)
        return render_template("fehler.html"), 500  # render fehler.html
    except (ValueError, TypeError, NameError):
        return render_template("fehler.html"), 500  # render fehler.html


# Rollen Dashboards


@app.route("/<name>/<rolle>/Dashboard")  # Dashboard
def Dashboard(name, rolle):  # Dashboard
    """
    The Dashboard function is called when the user wants to see the Dashboard of Dorfbewohner.
    It renders Dash_rolle.html and passes all variables to it.

    :param name: Get the name of the player
    :param rolle: Determine which dashboard is shown
    :return: The dash_rolle

    """
    # create a string with the name and the role
    with open("rollen_log.txt", "r", encoding="UTF8") as file:  # open the log file
        players_vorhanden = file.read()  # read the log file

    rolleAusLog = players_vorhanden.split(" = ")  # split the log file into a list
    rolleAusLog = rolleAusLog[1]

    if rolleAusLog == "Tot":
        return render_template("tot.html", name=name)  # render tot.html

    # if the name and the role are in the log file
    if werwolf.validiere_rolle(name, rolle) is True:
        try:  # try to get the role
            with open("rollen_log.txt") as players_log:  # open the log file
                players_log = players_log.readlines()  # read the log file

            nurNamen = []  # create a list with the names

            try:
                for line in players_log:  # for every line in the log file

                    if "*" in line:  # if the line contains a *
                        pass  # do nothing
                    else:  # if the line does not contain a *
                        line = line.split(" = ")  # split the line at the =
                        name_line = line[0]
                        # set the role to the second part of the line
                        auswahlRolle = line[1]

                        # if the role is not Tot or the role is not the Erzähler
                        if auswahlRolle not in ("Tot", "Erzaehler"):
                            # append the name to the list
                            nurNamen.append(name_line)

            except IOError:
                print(
                    "[Debug] Fehler beim Auslesen des rollen_logs in app.py line "
                    + str(getframeinfo(currentframe()).lineno - 1)
                )  # print the error

            # render Dash_rolle.html
            werwolf.in_log_schreiben(
                "Dorfbewohner Dashboard für "
                + name
                + " mit Rolle "
                + rolle
                + " angezeigt"
            )
            return render_template(
                "Dashboards/Dash_Dorfbewohner.html",
                name=name,
                rolle=rolle,
                names=players_log,
                nurNamen=nurNamen,
            )

        except Exception as e:
            return render_template("fehler.html"), 500  # render fehler.html

    else:
        # print the error
        print("Spieler oder Rolle falsch!")
        # render url_system.html
        return render_template("url_system.html", name=name, rolle=rolle)


@app.route("/<name>/<rolle>/Dashboard_sp")
def spezielles_Dashboard(name, rolle):
    """
    The spezielles_Dashboard function is called when a player opens his Dashboard.
    It takes two arguments: name and rolle. The function checks if the role is valid, then renders the spezielles Dashboard for that role.

    :param name: Get the name of the player who wants to see his dashboard
    :param rolle: Determine which dashboard is shown
    :return: The dashboard of the role

    """
    if rolle == "Tot":
        return render_template("fehler.html"), 500
    # create a string with the name and the role
    with open("rollen_log.txt", "r", encoding="UTF8") as file:  # open the log file
        players_vorhanden = file.read()  # read the log file

    rolleAusLog = players_vorhanden.split(" = ")  # split the log file into a list
    rolleAusLog = rolleAusLog[1]

    if rolleAusLog == "Tot":
        return render_template("tot.html", name=name)  # render tot.html
    # if the name and the role are in the log file
    if werwolf.validiere_rolle(name, rolle) is True:

        nurNamen = []  # create a list with the names

        if rolle == "Hexe":
            print("Hexe")
            with open("hexe_kann.txt", "r", encoding="UTF8") as file:
                hexe_kann = file.read()
                hexe_kann = str(hexe_kann)
                file.close()

    with open("rollen_log.txt") as players_log:  # open the log file
        players_log = players_log.readlines()  # read the log file

    for line in players_log:  # for every line in the log file

        if (
            "*" in line or "Tot" in line or "Erzaehler" in line
        ):  # if the line contains a *
            pass  # do nothing
        else:  # if the line does not contain a *
            line = line.split(" = ")  # split the line at the =
            name_line = line[0]
            # set the role to the second part of the line

            nurNamen.append(name_line)  # append the name to the list

    if rolle == "Hexe":
        with open("letzter_tot.txt", "r", encoding="UTF8") as file:
            letzter_tot = file.read()

        werwolf.in_log_schreiben(
            "Hexe Dashboard für " + name + " mit Rolle " + rolle + " angezeigt"
        )
        # render Dash_rolle.html
        return render_template(
            "Dashboards/Dash_" + rolle + ".html",
            name=name,
            rolle=rolle,
            names=players_log,
            nurNamen=nurNamen,
            hexe_kann=hexe_kann,
            letzter_tot=letzter_tot,
        )

    if rolle == "Armor":
        werwolf.in_log_schreiben(
            "Armor Dashboard für " + name + " mit Rolle " + rolle + " angezeigt"
        )
        return render_template(
            "Dashboards/Dash_" + rolle + ".html",
            name=name,
            rolle=rolle,
            names=players_log,
            nurNamen=nurNamen,
            armor_kann=werwolf.armor_darf_auswaehlen(),
        )
    # render Dash_rolle.html
    werwolf.in_log_schreiben(
        "Dashboard der Rolle "
        + rolle
        + " für "
        + name
        + " mit Rolle "
        + rolle
        + " angezeigt"
    )
    return render_template(
        "Dashboards/Dash_" + rolle + ".html",
        name=name,
        rolle=rolle,
        names=players_log,
        nurNamen=nurNamen,
    )


@app.route("/<name>/<rolle>/spiel_ende")
def spiel_ende(name, rolle):
    """
    The spiel_ende function is called when the game is over. It checks if Werwolf has won or lost and returns a
    template with the result.

    :param name: Identify the player
    :param rolle: Determine which template to display
    :return: The following:

    """
    with open("rollen_original.txt", "r", encoding="UTF8") as file:
        players_vorhanden = file.read()
        file.close()

        if werwolf.validiere_rolle_original(name, rolle) is True:
            if (
                "Werwolf" in players_vorhanden
                and "Dorfbewohner" in players_vorhanden
                or "Hexe" in players_vorhanden
                and "Werwolf" in players_vorhanden
                or "Seherin" in players_vorhanden
                and "Werwolf" in players_vorhanden
                or "Jaeger" in players_vorhanden
                and "Werwolf" in players_vorhanden
                or "Armor" in players_vorhanden
                and "Werwolf" in players_vorhanden
            ):
                werwolf.in_log_schreiben(
                    "Spiel noch nicht zuende für "
                    + name
                    + " mit Rolle "
                    + rolle
                    + " angezeigt"
                )
                return "Hallo " + escape(name) + ", das Spiel ist noch nicht beendet!"

            print("Spiel ist beendet!")

            if rolle == "Werwolf":
                if "Werwolf" in players_vorhanden:
                    werwolf.in_log_schreiben(
                        "Spiel beendet für "
                        + name
                        + " mit Rolle "
                        + rolle
                        + " angezeigt"
                    )
                    return render_template(
                        "gewonnen.html", name=name, rolle=rolle, unschuldig=0
                    )
                werwolf.in_log_schreiben(
                    "Spiel beendet für " + name + " mit Rolle " + rolle + " angezeigt"
                )
                return render_template(
                    "verloren.html", name=name, rolle=rolle, unschuldig=0
                )
            if "Werwolf" in players_vorhanden:
                werwolf.in_log_schreiben(
                    "Spiel beendet für " + name + " mit Rolle " + rolle + " angezeigt"
                )
                return render_template(
                    "verloren.html", name=name, rolle=rolle, unschuldig=1
                )
            werwolf.in_log_schreiben(
                "Spiel beendet für " + name + " mit Rolle " + rolle + " angezeigt"
            )
            return render_template(
                "gewonnen.html", name=name, rolle=rolle, unschuldig=1
            )
        return render_template("fehler.html"), 500


@app.route("/waehlen/<name>/<rolle>/<auswahl>")
def wahl(name, rolle, auswahl):
    """
    The wahl function is called when a user has selected a role and wishes to vote for another player.
    It takes the name of the player, their role and an option from the dropdown menu as arguments.
    If this is valid it will write that information into hat_gewaehlt.txt which is used by die_wahl() to check if someone has already voted.

    :param name: Identify the player
    :param rolle: Determine which role the player has
    :param auswahl: Store the users input
    :return: The following:

    """
    if rolle == "Tot":
        return render_template("warten.html")

    wort2 = name + " : "

    if werwolf.validiere_rolle(name, rolle) is True:

        with open("hat_gewaehlt.txt", "r+") as text:
            contents = text.read()

            if wort2 in contents:
                werwolf.in_log_schreiben(
                    "Wahl schon getätigt für "
                    + name
                    + " mit Rolle "
                    + rolle
                    + " angezeigt"
                )
                return render_template("wahl_doppelt.html")
            text.write(name + " : " + "\n")
            text.close()
            werwolf.in_log_schreiben(
                "Wahl getätigt für "
                + name
                + " mit Rolle "
                + rolle
                + " angezeigt, auswahl: "
                + auswahl
            )
            with open("abstimmung.txt", "a") as abstimmung:
                abstimmung.write(auswahl + "" + "\n")

                abstimmung.close()
                return render_template("Dashboards/status/warten.html")
    else:
        return render_template("fehler.html"), 500


# schlafen function


@app.route("/<name>/<rolle>/schlafen")  # route for the sleep function
def schlafen(name, rolle):  # function for the sleep function
    """
    The schlafen function is used to sleep the player.
    The function takes two parameters: name and rolle.
    If the string is in the log file, render schlafen.html.

    :param name: Get the name of the player
    :param rolle: Determine the role of the player
    :return: The sleep

    """
    if rolle == "Tot":
        return render_template("tot.html", name=name)

    # if the string is in the log file
    if werwolf.validiere_rolle(name, rolle) is True:
        try:
            with open("rollen_log.txt") as players_log:  # open the log file
                players_log = players_log.readlines()  # read the log file
            # render the sleep.html
            werwolf.in_log_schreiben(
                "Schlafen für " + name + " mit Rolle " + rolle + " angezeigt"
            )
            return render_template(
                "Dashboards/status/schlafen.html",
                name=name,
                rolle=rolle,
                names=players_log,
            )
        except (FileNotFoundError, IOError, PermissionError):
            return render_template("fehler.html"), 500  # render the fehler.html

    else:
        # print the error
        print("Spieler oder Rolle falsch!")
        # render the url_system.html
        return render_template("url_system.html", name=name, rolle=rolle)


# warten funktion


@app.route("/warten")  # route for the wait function
def warten():  # function for the wait function
    """
    The warten function is used to wait for all players to vote.
    It checks if all players have voted and then shows the results of the voting.

    :return: The template warten

    """
    i = 0  # set i to 0

    try:

        with open("rollen_log.txt", "r", encoding="UTF8") as text:
            for line in text:
                if "Tot" not in line and "Erzaehler" not in line and "*" not in line:
                    i = i + 1
            text.close()
        with open("abstimmung.txt", "r", encoding="UTF8") as text:
            # empty lines are not counted
            anzahl_stimmen = sum(1 for line in text if line.rstrip())

        text.close()
        print(anzahl_stimmen)
        print(i)
        if i == anzahl_stimmen:
            print("Alle Spieler haben gewaehlt")
            werwolf.in_log_schreiben("Alle Spieler haben gewaehlt")
            count = 0
            name_tot = ""
            maxCount = 0
            words = []

            file = open("abstimmung.txt", "r", encoding="UTF8")

            for line in file:

                string = line.lower().replace(",", "").replace(".", "").split(" ")
                for s in string:
                    words.append(s)

            for i in range(0, len(words)):
                count = 1
                for j in range(i + 1, len(words)):
                    if words[i] == words[j]:
                        count = count + 1

                if count > maxCount:
                    maxCount = count
                    name_tot = words[i]

            with open("rollen_log.txt", "r+") as fileTot:

                file_list = []
                counter_tot = 0

                for line in fileTot:
                    file_list.append(line)

                # print(file_list)

                name_tot = name_tot.strip("\n")
                name_tot = name_tot.replace("\n", "")

                while counter_tot < len(file_list):

                    print("Name Tot: " + name_tot + " =")

                    if name_tot in file_list[counter_tot]:
                        dffd = file_list[counter_tot].split(" = ")
                        new_line = dffd[0] + " = Tot \n"
                        # print(new_line)
                        file_list[counter_tot] = new_line
                        # print(file_list)

                    counter_tot = counter_tot + 1

            fileTot.close()
            with open("rollen_log.txt", "w", encoding="UTF8") as fileFinal:
                fileFinal.writelines(file_list)
            fileFinal.close()
            werwolf.schreibe_zuletzt_gestorben(name_tot)
            werwolf.in_log_schreiben("Ergebnis angezeigt für " + name_tot)
            return render_template("Dashboards/status/ergebnis.html", name_tot=name_tot)
        return render_template("Dashboards/status/warten.html")

    except (FileNotFoundError, IOError, PermissionError):
        return render_template("fehler.html"), 500  # render the fehler.html


# tot function

# route for the death function
@app.route("/<name>/<rolle>/<todesgrund>/tot")
def tot(name, rolle, todesgrund):  # function for the death function
    """
    The tot function is used to render the status page of a player who has been killed.
    It takes three arguments: name, rolle and todesgrund.
    name is the name of the player who was killed.
    rolle is either Werwolf or Dorfbewohner depending on what role they had in-game.
    todesgrund can be &quot;Werwolf&quot;, &quot;Abstimung&quot; or &quot;Hexe&quot;. It's used for different death reasons.

    :param name: Get the name of the player
    :param rolle: Determine the role of the player
    :param todesgrund: Set the death reason
    :return: The death page

    """
    # if the string is in the log file
    if werwolf.validiere_rolle(name, rolle) is True:
        try:  # try to get the role
            with open(
                "rollen_log.txt", "r", encoding="UTF8"
            ) as players_log:  # open the log file
                players_log = players_log.readlines()  # read the log file

            if todesgrund in (
                "Werwolf",
                "werwolf",
            ):  # if the death reason is a werewolf
                # set the death reason to a werewolf
                todesgrund = "Du wurdest von einem Werwolf getötet"
            # if the death reason is a abstimulation
            elif todesgrund in ("Abstimung", "abstimmung"):
                # set the death reason to a abstimulation
                todesgrund = "Du wurdest in Folge einer Abstimmung getötet"
            elif todesgrund == "Hexe":  # if the death reason is a witch
                todesgrund = (
                    "Du wurdest von der Hexe getötet"  # set the death reason to a witch
                )
            else:
                todesgrund = (
                    "Du wurdest getötet"  # set the death reason to a normal death
                )
            # rendert die Seite zum Status Tot
            werwolf.in_log_schreiben(
                "Tot für " + name + " mit Rolle " + rolle + " angezeigt"
            )
            return render_template(
                "Dashboards/status/tot.html",
                name=name,
                todesgrund=todesgrund,
            )

        except (FileNotFoundError, IOError, PermissionError):
            # rendert die Seite zum Status Fehler
            return render_template("fehler.html"), 500

    else:
        # print the error
        print("Spieler oder Rolle falsch!")
        # render the url_system.html
        return render_template("url_system.html", name=name, rolle=rolle)


# kick function


@app.route("/<name>/<rolle>/kick/")  # route for the kick function
def rausschmeissen(name, rolle):  # function for the kick function
    """
    The rausschmeissen function is used to kick a player from the game.
    It takes two arguments: name and rolle.
    If the function is called with valid arguments, it will remove the player from
    the game and write an entry in log_file.

    :param name: Render the kick
    :param rolle: Specify the role of the player that is kicked
    :return: The kick function

    """
    if werwolf.validiere_rolle(name, rolle) is True:
        print("Spieler vorhanden")  # print the string
        try:
            with open(
                "rollen_log.txt", "r", encoding="UTF8"
            ) as players_log:  # open the log file
                players_log = players_log.readlines()  # read the log file
            # render the rausschmeissen.html

            werwolf.toete_spieler(name)
            werwolf.in_log_schreiben(
                "Spieler " + name + " rausgeschmissen, er hatt die Rolle " + rolle
            )
            return render_template(
                "rausschmeissen.html", name=name, rolle=rolle, names=players_log
            )
        except IOError as e:

            return render_template("fehler.html"), 500  # render the fehler.html

    else:
        # print the error
        print("Spieler oder Rolle falsch!")
        # render the url_system.html
        return render_template("url_system.html", name=name, rolle=rolle)


# wahlbalken


@app.route("/wahlbalken/")  # route for the wahlbalken function
def wahlbalken():
    """
    The wahlbalken function renders the wahlbalken.html page, which is used to select a player for the current round.

    :return: The wahlbalken

    """
    with open("rollen_log.txt", encoding="UTF8") as players_log:  # open the log file
        players_log = players_log.readlines()  # read the log file

    print(players_log)

    print("Test")

    nurNamen = []  # create a list for the names

    try:
        for line in players_log:  # for every line in the log file

            if "*" in line:  # if the line contains a *
                pass  # do nothing
            else:  # if the line does not contain a *
                line = line.split(" = ")  # split the line at the =
                name = line[0]  # get the name
                auswahlRolle = line[1]  # get the role

                # if the role is not dead or the narrator
                if auswahlRolle not in ("Tot", "Erzaehler"):
                    nurNamen.append(name)  # append the name to the list

        # render the wahlbalken.html
        return render_template("wahlbalken.html", names=nurNamen)

    except Exception as e:
        return render_template("fehler.html"), 500  # render the fehler.html


@app.route("/wahlstatus")  # route for the wahlstatus function
def wahl_stats():
    """
    The wahl_stats function counts the number of times a name appears in the abstimmung.txt file and returns
    the name with the most votes. It also writes this name to wahl_zuletzt_gestorben.txt.

    :return: The most common name in the text

    """
    anzahl = 0
    name_tot = ""
    maxCount = 0
    words = []

    file = open("abstimmung.txt", "r", encoding="UTF8")

    for line in file:

        string = line.lower().replace(",", "").replace(".", "").split(" ")
        for s in string:
            words.append(s)

    for i in range(0, len(words)):
        anzahl = 1
        for j in range(i + 1, len(words)):
            if words[i] == words[j]:
                anzahl = anzahl + 1

        if anzahl > maxCount:
            maxCount = anzahl
            name_tot = words[i]

            werwolf.schreibe_zuletzt_gestorben(name_tot)

    return render_template("wahlstatus.html", name_tot=name_tot)


@app.route("/sehen/<name>/<rolle>/<auswahl>")
def sehen(name, rolle, auswahl):
    """
    The sehen function allows the Seherin to see the role of a player.
    The function takes three arguments: name, rolle and auswahl.
    name is the name of the seherin, rolle is her role and auswahl is
    the player she wants to check.

    :param name: Identify the player
    :param rolle: Check if the player is a werewolf or not
    :param auswahl: Select the role you want to see
    :return: The role of the player that was chosen

    """
    if werwolf.validiere_rolle(name, rolle) is True:
        with open(
            "rollen_log.txt", encoding="UTF8"
        ) as players_log:  # open the log file
            players_log = players_log.readlines()  # read the log file
        for line in players_log:
            if auswahl in line:
                ergebnis = line
                ergebnis = ergebnis.replace("=", "hat die Rolle")
                werwolf.in_log_schreiben(
                    "Seherin "
                    + name
                    + "hat die Rolle von "
                    + auswahl
                    + " gesehen "
                    + ergebnis.replace(name + " hat die Rolle", "")
                )
                return render_template(
                    "Dashboards/status/sehen.html", ergebnis=ergebnis
                )
    return render_template("fehler.html"), 500


@app.route("/weiterleitung/<target>")
def weiterleitung(target):
    """
    The weiterleitung function is used to redirect the user to another page.
    It takes one argument, which is the target of the redirection.


    :param target: Redirect to another page
    :return: The rendered template &quot;weiterleitung

    """
    werwolf.in_log_schreiben("Weiterleitung auf " + target)
    return render_template("weiterleitung.html", target=target)


@app.route("/<name>/<rolle>/<auswahl>/wer_tot")
def wer_tot(name, rolle, auswahl):
    """
    The wer_tot function is used to add a player to the list of players who have voted.
    It takes three arguments: name, rolle and auswahl.
    The function checks if the player has already voted,
    and if not it adds them to hat_gewaehlt.txt and writes their vote in abstimmung.txt.

    :param name: Identify the player
    :param rolle: Check if the player has already chosen a role
    :param auswahl: Store the selected player
    :return: A message that the user has already voted

    """
    with open("rollen_log.txt", "r", encoding="UTF8") as file:  # open the log file
        players_vorhanden = file.read()  # read the log file
    if werwolf.validiere_rolle(name, rolle) is True:
        with open("hat_gewaehlt.txt", "r", encoding="UTF8") as f:
            if name + " : " in f.read():
                return render_template("wahl_doppelt.html")
            auswahl = auswahl.strip()  # erase the whitespace %20
            if auswahl in players_vorhanden:
                print("Eine legetime Auswahl wurde getroffen!")
                with open("abstimmung.txt", "a") as abstimmung:
                    abstimmung.write(auswahl + "\n")
                abstimmung.close()
                with open("hat_gewaehlt.txt", "a") as hat_gewaehlt:
                    hat_gewaehlt.write(name + " : " + "\n")
                    return render_template("Dashboards/status/wer_wahl_warten.html")
            else:
                return render_template("fehler.html"), 500
    else:
        return render_template("url_system.html", name=name, rolle=rolle)


@app.route("/wer_wahl_warten")
def wer_wahl_warten():
    """
    The wer_wahl_warten function is used to display the wer_wahl_warten.html template, which is displayed when a player has voted for a player to be killed.

    :return: The current status of the voting

    """
    with open("hat_gewaehlt.txt", "r+") as hat_gewaehlt:
        wer_anzahl_stimmen = sum(1 for line in hat_gewaehlt if line.rstrip())
        if wer_anzahl_stimmen == 4:

            count = 0
            name_tot = ""
            maxCount = 0
            words = []

            file = open("abstimmung.txt", "r", encoding="UTF8")

            for line in file:

                string = line.lower().replace(",", "").replace(".", "").split(" ")
                for s in string:
                    words.append(s)

            for i in range(0, len(words)):
                count = 1
                for j in range(i + 1, len(words)):
                    if words[i] == words[j]:
                        count = count + 1

                if count > maxCount:
                    maxCount = count
                    name_tot = words[i]

            with open("rollen_log.txt", "r+") as fileTot:

                file_list = []
                counter_tot = 0

                for line in fileTot:
                    file_list.append(line)

                # print(file_list)

                name_tot = name_tot.strip("\n")
                name_tot = name_tot.replace("\n", "")

                while counter_tot < len(file_list):

                    print("Name Tot: " + name_tot + " =")

                    if name_tot in file_list[counter_tot]:
                        dffd = file_list[counter_tot].split(" = ")
                        new_line = dffd[0] + " = Tot \n"
                        # print(new_line)
                        file_list[counter_tot] = new_line
                        # print(file_list)

                    counter_tot = counter_tot + 1

            fileTot.close()
            with open("rollen_log.txt", "w") as fileFinal:
                fileFinal.writelines(file_list)
            fileFinal.close()

            werwolf.schreibe_zuletzt_gestorben(name_tot)

            return render_template(
                "Dashboards/status/wer_wahl_ergebnis.html", name_tot=name_tot
            )
        return render_template("Dashboards/status/wer_wahl_warten.html")


@app.route("/<name>/<rolle>/heilen/<auswahl>")
def heilen(name, rolle, auswahl):
    """
    The heilen function allows a witch to heal someone.



    :param name: Identify the witch
    :param rolle: Check if the person that wants to heal is a witch
    :param auswahl: Replace the name of the person to be healed in the rollen_original
    :return: The dashboard dorfbewohner

    """
    if (
        werwolf.validiere_rolle(name, rolle) is True
        and werwolf.hexe_darf_heilen() is True
    ):
        counter = 1
        with open("rollen_original.txt", "r", encoding="UTF8") as file:
            file_list = ["*********************\n"]

            for line in file:
                file_list.append(line)

        while counter < len(file_list):
            if auswahl in file_list[counter]:
                file_list[counter] = file_list[counter].replace(name, auswahl)
                counter = counter + 1
            else:
                counter = counter + 1
        file = open("rollen_log.txt", "w")

        file.writelines(file_list)

        werwolf.hexe_verbraucht("heilen")
        werwolf.in_log_schreiben("Hexe " + name + " hat " + auswahl + " geheilt")
        return render_template("Dashboards/Dash_Dorfbewohner.html")
    return render_template("fehler.html"), 500


# TODO: #76 Sicherheitsabfrage bei der Anzeige des Logs
@app.route("/log")
def log_ansehen():
    """
    The log_ansehen function will take the logfile.txt and put it into a list, then print out the list in html format.

    :return: The logfile

    """
    with open("logfile.txt", "r", encoding="UTF8") as file:
        # put the file into a list
        file_list = []
        for line in file:
            file_list.append(line)
        # print the list
        print(file_list)
        # return the list

        return render_template("log.html", log=file_list)


@app.route("/<token>/status")
def zum_ziel(token: str):
    if werwolf.validiere_token(token):

        # send the status as a response
        try:
            return redirect(werwolf.erhalte_ziel(token))
        except AttributeError:

            return render_template("403.html"), 403


@app.route("/noscript")
def noscript():
    """
    The noscript function is called when the user requests a page that requires JavaScript.
    It returns a template containing only an information message about this fact.

    :return: The noscript

    """
    werwolf.in_log_schreiben("Noscript wurde aufgerufen")
    return render_template("noscript.html")


# context processor


@app.context_processor
def inject_now():
    """
    The inject_now function injects the current date and time into the context.
       This is useful for dynamic data that requires timestamps.

    :return: A dictionary with a key of now and the value being the current time

    """
    return {"now": datetime.utcnow()}


# sentry error handler
@app.errorhandler(500)
def server_error_handler(error):
    """
    The server_error_handler function is used to render a custom error page when the server encounters an error.
    It is passed as the handler argument to app.register_error_handler

    :param error: Pass the error message to the template
    :return: A template fehler

    """
    return render_template("fehler.html"), 500


@app.errorhandler(404)
def page_not_found(error):
    """
    The page_not_found function is used to render a custom error page when the server encounters an error.
    It is passed as the handler argument to app.register_error_handler

    :param error: Pass the error message to the template
    :return: A template 404

    """
    return render_template("404.html"), 404


@app.errorhandler(403)
def forbidden(error):
    """
    The forbidden function is used to render a custom error page when the server encounters an error.
    It is passed as the handler argument to app.register_error_handler

    :param error: Pass the error message to the template
    :return: A template 403

    """
    return render_template("403.html"), 403


if __name__ == "__main__":
    app.run(debug=True)
