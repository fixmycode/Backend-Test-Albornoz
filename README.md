![Nora's](static/img/logo.png)

# Nora's Meal Service

Are you tired of having to contact all your company's employees manually to ask them what they want to eat today? Nora is a service that allows you to manage employee meals using the *Slack* messaging platform.

## Prerequisites

* Python 3.8.1+
* Redis 4.0.9+
* An Slack account

## Install

Clone the repo to a folder on your machine or server. Then go inside the repo's folder and run the following commands

```bash
# creates a new virtual environment and activate it
python -m env env/
source ./env/bin/activate

# install the required packages
pip install -r requirements.txt
```

## Service Configuration

Nora needs to be able to speak to your Slack workspace, so it needs Slack credentials. You may need to create a new Slack app by following [this link](https://api.slack.com/apps?new_app=1) or use a set of credentials you already have.

You can set your information in environment variables on your machine or use a `.env` configuration file.

```bash
export SLACK_CLIENT_ID=99999.999999
export SLACK_CLIENT_SECRET=abcdefghijk
```

That's all the information you need to start, but Nora has a lot of configuration options for you to customize your service, you can read more about them [here](#settings).

One of the settings you shoud keep in mind is `NORA_URL`: This will be the URL that your employees will receive in their Slack messages and should point to your service.

```bash
export NORA_URL=https://nora.cornershop.io
```

If you wish to save this configuration in a file, create a file named `.env` in your service folder and write the values using the same notation as in `export`:

    SLACK_CLIENT_ID=99999.999999
    SLACK_CLIENT_SECRET=abcdefghijk
    NORA_URL=https://nora.cornershop.io

## Slack configuration

Slack will try to call your service to authenticate yourself, so you need to give them some information. In the [Slack API website](https://api.slack.com/apps), go to **Your App > OAuth & Permissions > Redirect URLs** and add a new Redirect URL that points to the following endpoint: `/slack/auth`. For example, if your app is running at `https://nora.cornershop.io`, you will enter:

    https://nora.cornershop.io/slack/auth

Save the redirect URL, and that's it.

> **Note:** if you're using the default configuration, your service will try to run in `your-ip-address:8000`, so your redirect URL will be `http://your-ip-address:8000/slack/auth`.

## Create the database

After configuring your service and before you run it, you neet to create the database. To use your configuration, you may want to use `honcho`, an utility that will take care of loading your configuration and managing the processes needed for the service to work. From the repo folder, you'll use the following command:

    honcho run ./manage.py migrate

`honcho` will pick up your configuration and build the database. it will appear as a file called `db.sqlite3`. This has to be done only once, or if you change the database configuration.

## Running your service

To start the service, you'll want to use `honcho` again:

    honcho start

This will start the service process and the background worker needed for the service to function properly. If you want to know what this command is running on your machine you can take a look at the [Procfile](Procfile) document. To stop all the processes, you can use `Ctrl + C`.

You can now point your browser to the service's address and begin using it.

# Usage

## Menus

In the Menus view, you can see a list of the menus for each date, note here that it's perfectly fine to have more than one menu in a single date. You can create a new menu by pressing the **New Menu** button on the top right corner. Menus have two main elements:

* **Options**: This is a list of options that the employees can choose between for their meal.
* **Date**: This is the day that the employee will receive the message with the options.

You can `edit` and `delete` future menus without notifying your employees, but once the date comes, the service will notify the employees each time you make a change to a present menu.

## Orders

In the Orders view, you can see the list of orders for a given date, you can also select the date by using the dropdown at the top of the list. Orders can be in one of three states:

* **Pending**: The employee received your message but he has yet to select what to eat. You can see how many pending orders you have on the top right corner.
* **Active**: The employee has made a choice about what he wants to eat. You can see a list of the active orders on the middle of the screen, if you choose the `Done` action on the right, this will notify the employee that you're preparing the meal and he can't change its mind now.
* **Completed**: These are the orders that you have labeled as `Done`.

## The Message

The employees will receive a message with the meal options for each menu published on a given date. You can customize the time of day that the employees will receive this message by changing the [settings](#settings). In this message there's a link that allows the employee to choose whichever option they want for their meal and also add any notes (*ex: "sauce on the side"*) to customize their choice.

Each time the employee saves their order, the message will get updated to reflect their selection, and it will show a green check mark ✅ on the option they choose. When you mark their order as `Done` in the Orders view, the message will show two green marks ✅✅, and will also close their order.

> Hello, Pablo Albornoz!  
> This is the menu for today, March 1, 2021 😀
>
> **Option 1: Seafood mix** ✅
>
> Option 2: Caesar salad
>
> Option 3: Beef and rice
>
> Make your selection by following [this link](#the-message)  
> Have a nice day! 😊

Orders will be automatically closed at 11am (you can change this in the [settings](#settings)). The order page shows a countdown so the employee knows he needs to make a choice quickly. After the order is closed the employees can't change their order.

# Testing

Install the testing utilities by running the following command:

```bash
source ./env/bin/activate # ensure your virtual environment is active
pip install -r requirements.dev.txt
```

To run the tests you can use `pytest`. Note that the tests will avoid contacting Slack, so you can use any credentials you want.

```bash
pytest -v # will use the present .env file
pytest -v --envfile .env
pytest -v --envfile .env.test
```

# Settings

Below there's a list of things you can set using the configuration file, and their default values:

## Nora-specific

```ini
NORA_URL=https://nora.cornershop.io 
#The URL that will be sent on the message to the employees, should direct them to your service

NORA_NOTIFY_HOUR=7 
#The hour of the day in which the service should send the reminder to the employees. Can be set to -1 to send the message immediately after creating the menu. Ideal for testing.

NORA_NOTIFY_MINUTE=0
#Integer between 0-59 to describe when in the hour to send the reminders.

NORA_THRESHOLD=11
#Integer between 0-23 in which the service stops receiving orders for the day.

NORA_ONLY_LOCALS=false
#Restricts the user discovery to just Slack users which timezone matches the service's. This way you can filter for employees from a certain region, like Chile.

NORA_REDIS_SERVER=localhost:6379/0
#Points to an instance of Redis, by default it assumes that Redis is running on the same machine but you can change it to point to a remote service.

NORA_SECRET_KEY=super-secret-key
#Used by the framework to establish session keys, keep it secret, keep it safe.

NORA_DEBUG=true
#Shows debug information, also allows you to serve static files locally, so its a good default. Otherwise you will have to serve your own static files, which is out of the scope of this manual.
```

## Slack

```ini
SLACK_CLIENT_ID=
#Required. The client ID for your Slack app, see service configuration.

SLACK_CLIENT_SECRET=
#Required. The client secret for your Slack app, see service configuration.

SLACK_USE_REMINDERS=false
#Use the Slackbot's reminder interface to notify the employees. As reminders can't be updated, it will disable a lot of the app functionality, but it should work.
```