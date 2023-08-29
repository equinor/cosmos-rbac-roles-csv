import subprocess
import json
import csv

# Add known group ID's here, and their names in the array below such that the indices match. I.e known_ad_groups[0] and known_ad_group_names[0] correspond
known_ad_groups = []
known_ad_group_names = []


def getResourceGroupName(env):
    return f"MyResourceGroup{env}"


def getCosmosAccountName(env):
    return f"my-cosmos-account{env.lower()}"


def roleName(roleDefinition):
    # ID 00..02 = readwrite, ID 00..01 == readonly. Since there are only two built-in roles, it's either 02 or 01
    # Modify this to a lookup if you have multiple roles
    return (
        "readwrite"
        if roleDefinition.rsplit("/", 1)[1] == "00000000-0000-0000-0000-000000000002"
        else "read only"
    )


def getCosmosRoles(env):
    print(f"Working on {env}")
    cmd_process = subprocess.Popen(
        [
            "az",
            "cosmosdb",
            "sql",
            "role",
            "assignment",
            "list",
            "-a",
            getCosmosAccountName(env),
            "-g",
            getResourceGroupName(env),
        ],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assignedRoles = []

    assignments = json.loads(cmd_process.stdout.read())
    for x in assignments:
        # Dirty hack: If it's not in the set of known groups, we instead look it up via the Azure CLI
        try:
            index_of_group = known_ad_groups.index(x["principalId"])
            assignedRoles.append(
                [known_ad_group_names[index_of_group], roleName(x["roleDefinitionId"])]
            )
        except ValueError:
            cmd_process = subprocess.Popen(
                ["az", "ad", "sp", "show", "--id", x["principalId"]],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            principal = json.loads(cmd_process.stdout.read())
            assignedRoles.append(
                [principal["displayName"], roleName(x["roleDefinitionId"])]
            )
    return assignedRoles


# Add your enviroments here
envs = ["Dev"]
roles = [getCosmosRoles(env) for env in envs]

# Write the result to a CSV-file
with open("cosmos-roles.csv", "w", newline="") as csvfile:
    csv_writer = csv.writer(csvfile, delimiter=",", dialect="excel")
    for i in range(0, len(roles)):
        csv_writer.writerow([envs[i]])
        [csv_writer.writerow(r) for r in roles[i]]
        csv_writer.writerow("")
