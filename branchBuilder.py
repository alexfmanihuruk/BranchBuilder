import sys

from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater
from telegram.ext.dispatcher import run_async

import config
import jenkins
import strings
import gitlab

reload(sys)
sys.setdefaultencoding('utf-8')

# jenkins server instance
server = None
# record jenkins branch list
branches = []


def init(url, username, token):
    global server
    server = jenkins.Jenkins(url, username, token)
    user = server.get_whoami()
    print '[Jenkins bot] loggined url: %s, user: %s' % (url, user['id'])
    global jobName 
    jobName = config.jenkins_job
    global gl
    gl = gitlab.Gitlab(config.gitlab_url, config.gitlab_token, api_version=4)
    global project
    project = gl.projects.get(config.gitlab_repo)
    global branches
    branches = project.branches.list()


def refresh():
    init()

   
def isValidBranchName(branchName):
   #bot.sendMessage(update.message.chat_id, text='bra')
   for branch in branches:
       #bot.sendMessage(update.message.chat_id, text='bra')
       if branch.name == branchName:
           return True
   print strings.INVALID_BRANCH_NAME
   return False


@run_async
def listBranches(bot, update):
   s = 'branch list'
   for r in branches:
      s = '\n'.join([s, '%s ' % (r.name)])
   bot.sendMessage(update.message.chat_id, text=s)


@run_async
def startBuildJob(bot, update, args):
    if args:
        branchName = args[0]
    else:
        branchName = ''
    if not isValidBranchName(branchName):
        bot.sendMessage(update.message.chat_id, text=strings.INVALID_BRANCH_NAME)
        return

    if not isAlreadyBuilding(jobName):
        print 'building ' + branchName
        server.build_job(jobName,{'BRANCH': branchName})
        s = 'start building ' + jobName +  ' from branch ' + branchName
        print s
        bot.sendMessage(update.message.chat_id, text=s)
        return
    else:
        s = jobName + string.ALREADY_BUILD
        print s
        bot.sendMessage(update.message.chat_id, text=s)
        return


def isAlreadyBuilding(jobName):
    running_builds = server.get_running_builds()
    for r in running_builds:
        if r['name'] == jobName:
            return True
    return False


@run_async
def stopBuildJob(bot, update):
#    bot.sendMessage(update.message.chat_id, text='a')
    running_builds = server.get_running_builds()
    for r in running_builds:
#        bot.sendMessage(update.message.chat_id, text='b')
        if r['name'] == jobName:
            s = 'stop %s#%d, %s' % (r['name'], r['number'], r['url'])
            print s
            server.stop_build(jobName, r['number'])
            bot.sendMessage(update.message.chat_id, text=s)
            return

    s = jobName + strings.NO_JOB_BUILDING
    print s
    bot.sendMessage(update.message.chat_id, text=s)

def error(bot, update, error):
    print 'Update "%s" caused error "%s"' % (update, error)


def help(bot, update):
    s = '\n'.join(
            ['/help # get help', '/list # list all branches',
                '/build branchName # build vaesdothrak from branchName',
                '/stop # stop build '])
    bot.sendMessage(update.message.chat_id, text=s)


def main():
    # init jenkins
    init(config.jenkins_url, config.jenkins_username, config.jenkins_token)
    # Create the EventHandler and pass it your bot's token
    updater = Updater(config.telegram_bot_token)
    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # add command handlers
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("list", listBranches))
    dp.add_handler(CommandHandler("build", startBuildJob, pass_args=True))
    dp.add_handler(CommandHandler("stop", stopBuildJob)) 
    # log all errors
    dp.add_error_handler(error)

    # start bot
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
