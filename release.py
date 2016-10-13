import os
import subprocess
import optparse
import pdb

file_dir = os.path.dirname(os.path.realpath(__file__))
release_folder = "0B1eEAP4_65xcVlNXT0szbHliaEk"
debug_folder = "0B5_4x43qwPAPMlJRZXl0dTJWVEU"

def nav_file():
    os.chdir(file_dir)

def nav_bee():
    nav_file()
    os.chdir('..')

def auth_drive():
    nav_file()
    from pydrive.auth import GoogleAuth
    from pydrive.drive import GoogleDrive

    gauth = GoogleAuth()
    gauth.LocalWebserverAuth() # Creates local webserver and auto handles authentication

    return GoogleDrive(gauth)

def upload_drive(drive, directory, version, folder):
    nav_bee()
    release_types = ["development", "staging", "production"]
    for release_type in release_types:
        f = drive.CreateFile({"title": "HBDroidBee-" + release_type + "-v" + version + ".apk", "parents": [{"kind": "drive#fileLink","id": folder}]})
        f.SetContentFile(directory + 'HBDroidBee-' + release_type + '-v' + version + '.apk') # Read local file
        f.Upload()

def rebase_branches(branch, rebase_branch):
    nav_bee()
    _rebase(branch, rebase_branch)
    os.chdir('../HB-Droid-Core/')
    _rebase(branch, rebase_branch)

def _rebase(branch, rebase_branch):
    os.system('git checkout {}'.format(branch))
    os.system('git pull')
    os.system('git checkout {}'.format(rebase_branch))
    os.system('git pull')
    os.system('git checkout {}'.format(branch))
    os.system('git merge {}'.format(rebase_branch))
    os.system('git push origin {}'.format(branch))

def checkout(branch):
    # make sure that we've fetched everything
    nav_bee()
    os.system('git checkout {}'.format(branch))
    os.system('git fetch')
    os.system('git pull')
    os.chdir('../HB-Droid-Core/')
    os.system('git checkout {}'.format(branch))
    os.system('git fetch')
    os.system('git pull')
    os.chdir('../HB-Droid-Bee/')

# execute the gradle task
def build_release():
    nav_bee()
    os.system("./gradlew assembleRelease crashlyticsUploadDistributionDevelopmentRelease crashlyticsUploadDistributionStagingRelease crashlyticsUploadDistributionProductionRelease  --stacktrace")

def build_debug():
    nav_bee()
    os.system("./gradlew assembleDebug")

def tag(v, branch):
    nav_bee()
    os.system('git add -A')
    os.system('git commit -m "release v"' + v)
    os.system('git push origin {}'.format(branch))
    os.system('git tag -a REL_' + v + ' -m "release v' + v + '"')
    os.system('git push origin REL_' + v + '')
    os.chdir('../HB-Droid-Core/')
    os.system('git tag -a REL_' + v + '_bee -m "release v' + v + '"')
    os.system('git push origin REL_' + v + '_bee')
    os.chdir('../HB-Droid-Bee/')

def update_version(v_new, branch):
    nav_bee()
    v_build = subprocess.check_output("cat HBDroidBee/build.gradle | grep versionBuild | grep -o -E '\d.*$'", shell=True).strip()
    v_build_new = int(v_build) + 1
    update_build = "sed -i '' 's/versionBuild[[:space:]][[:digit:]]*/versionBuild {}/g' HBDroidBee/build.gradle".format(v_build_new)
    subprocess.call(update_build, shell=True)
    os.system('git add -A')
    os.system('git commit -m "update version to ' + v_new + '"')
    os.system('git push origin {}'.format(branch))

version_format = "{0}.{1}.{2}.{3}"

def version():
    nav_bee()
    v_major = subprocess.check_output("cat HBDroidBee/build.gradle | grep versionMajor | grep -o -E '\d.*$'", shell=True).strip()
    v_minor = subprocess.check_output("cat HBDroidBee/build.gradle | grep versionMinor | grep -o -E '\d.*$'", shell=True).strip()
    v_patch = subprocess.check_output("cat HBDroidBee/build.gradle | grep versionPatch | grep -o -E '\d.*$'", shell=True).strip()
    v_build = subprocess.check_output("cat HBDroidBee/build.gradle | grep versionBuild | grep -o -E '\d.*$'", shell=True).strip()
    v = version_format.format(v_major, v_minor, v_patch, v_build)
    v_new = version_format.format(v_major, v_minor, v_patch, int(v_build) + 1)
    return (v, v_new)

def release_notes(last_tag, version):
    nav_bee()
    notes = "Bee App version v{0}\n\n{1}\n" \
        + "Please send your feedback to:\n" \
        + "elaine@honestbee.com"

    log_diff = "git log {0}..HEAD".format(last_tag)

    diff_notes = subprocess.check_output(log_diff + " | grep -o -E '[A-Z]+-[0-9]+' | tr '[:lower:]' '[:upper:]' | sort | uniq | xargs -n 1 jira-cli view --oneline | gsed -r 's/\[(\w|\s)*][[:space:]]$//g'", shell=True)
    new_notes = notes.format(version, diff_notes)
    with open('release_notes.txt', 'wr') as f:
        f.write(new_notes)
    return new_notes

def update_tickets(last_tag, current_version):
    subprocess.check_output("git log {}..HEAD | grep -o -E '[A-Z]+-[0-9]+' | tr '[:lower:]' '[:upper:]' | sort | uniq | xargs -n 1 jira-cli update --transition='Backlog'".format(last_tag), shell=True)
    subprocess.check_output("git log {}..HEAD | grep -o -E '[A-Z]+-[0-9]+' | tr '[:lower:]' '[:upper:]' | sort | uniq | xargs -n 1 jira-cli update --transition='start development'".format(last_tag), shell=True)
    subprocess.check_output("git log {}..HEAD | grep -o -E '[A-Z]+-[0-9]+' | tr '[:lower:]' '[:upper:]' | sort | uniq | xargs -n 1 jira-cli update --transition='for code review'".format(last_tag), shell=True)
    subprocess.check_output("git log {}..HEAD | grep -o -E '[A-Z]+-[0-9]+' | tr '[:lower:]' '[:upper:]' | sort | uniq | xargs -n 1 jira-cli update --transition='qa review'".format(last_tag), shell=True)
    subprocess.check_output("git log {0}..HEAD | grep -o -E '[A-Z]+-[0-9]+' | tr '[:lower:]' '[:upper:]' | sort | uniq | xargs -n 1 jira-cli update --fix-version='{1}'".format(last_tag, current_version), shell=True)

parser = optparse.OptionParser()
parser.add_option("-t", "--last-tag", dest="last_tag", help="the last tagged version")
parser.add_option("-b", "--branch", dest="branch", help="the branch that you want to release")
parser.add_option("-r", "--rebase-from", dest="rebase_branch", help="the branch that you want to rebase against")
opts, args = parser.parse_args()

branch = opts.branch or 'development'
rebase_branch = opts.rebase_branch

print "Making sure that the branch is up to date..\n"
checkout(branch)

if rebase_branch:
    print "Rebasing branch..\n"
    rebase_branches(branch, rebase_branch)

v, v_new = version()
print "Your current version: " + v
print "Your new version: " + v_new
new_notes = release_notes(opts.last_tag, v)

print "Releasing with the release notes: " + new_notes + "\n"

raw_input("Press enter to confirm that you have read the new release notes")

build_release()
print "Updating tickets.."
update_tickets(opts.last_tag, v)

drive = auth_drive()
print "Uploading release to drive.."
upload_drive(drive, "HBDroidBee/build/outputs/apk/", v, release_folder)
build_debug()
drive = auth_drive()
print "Uploading debug to drive.."
upload_drive(drive, "HBDroidBee/build/outputs/apk/", v, debug_folder)

raw_input("Press enter to confirm that you want to tag this version")
tag(v, branch)

raw_input("Press enter to confirm that you want to update this version")
update_version(v_new, branch)

