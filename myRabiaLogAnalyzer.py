import csv
import itertools
import matplotlib.pyplot as plt
from matplotlib.ticker import LogFormatter


zip_longest = itertools.zip_longest
REDIS_LOGS_DIR = "logs/sinrabia/"
RABIA_LOGS_DIR = "logs/rabia/"
REDIS_LOGFILE = "redislog"
RABIA_LOGFILE = "rabialog"
LOG_EXTENSION = ".log"

def oldreadLogFiles(logfile1, logfile2, logfile3):
    f1 = open(logfile1)
    f2 = open(logfile2)
    f3 = open(logfile3)

    csv_f1 = csv.reader(f1, delimiter=" ")
    csv_f2 = csv.reader(f2, delimiter=" ")
    csv_f3 = csv.reader(f3, delimiter=" ")

    countDiff = 0
    numLine = 1
    setCmds = 0
    getCmds = 0
    for rowf1, rowf2, rowf3 in zip_longest(csv_f1, csv_f2, csv_f3):
        numLine += 1
        if len(rowf1) <= 1: continue    # Blank line [] or ['OK']
        if rowf1[3] == "hello" or rowf1[3] == "ping": continue

        # idx '3' is type operation: set | get
        opR1, opR2, opR3 = rowf1[3], rowf2[3], rowf3[3]
        if opR1 != opR2 or opR1 != opR3 or opR2 != opR3:
            print("Tipo Operacion diferente: Op# " + str(numLine))
            countDiff += 1
            continue

        # At this point all replicas have the same kind of operation
        # If operation is Get -> inspect consistency
        if len(rowf1) == 5:
            # Get Command
            getCmds += 1
            # Check key of get operation
            keyR1, KeyR2, KeyR3 = rowf1[4], rowf2[4], rowf3[4]
            if keyR1 != KeyR2 or keyR1 != KeyR3 or KeyR2 != KeyR3:
                print("Operacion GET diferente: Op# " + str(numLine))
                countDiff += 1
                continue
        # If operations is Set -> inspect consistency
        elif len(rowf1) == 6:
            # Set Command
            setCmds += 1
            # Check key of set operation
            keyR1, KeyR2, KeyR3 = rowf1[4], rowf2[4], rowf3[4]
            if keyR1 != KeyR2 or keyR1 != KeyR3 or KeyR2 != KeyR3:
                print("Operacion SET diferente key: Op# " + str(numLine))
                countDiff += 1
                continue
            # Check value of set operation
            valR1, valR2, valR3 = rowf1[5], rowf2[5], rowf3[5]
            if valR1 != valR2 or valR1 != valR3 or valR2 != valR3:
                print("Operacion SET diferente value: Op# " + str(numLine))
                countDiff += 1
                continue
        print(rowf1)
        numLine += 1

    print("Total Sets Commands:" + str(setCmds))
    print("Total Gets Commands:" + str(getCmds))
    print("Total Commands: " + str(getCmds + setCmds))
    print("Total Inconsistencias: " + str(countDiff))

    f1.close()
    f2.close()
    f3.close()
    return

'''
newreadLogFiles: read log files and generate a list of operations executed by each replica
input: list of log files
output: decisions of each replicas. Eg [decisionsR1, decisionsR2, decisionsR3]
'''
def readLogFiles(listLogFiles):
    # Open files
    listCsvReaders = []
    filesObjects = []
    for file in listLogFiles:
        f = open(file)
        filesObjects.append(f)
        csvReader = csv.reader(f, delimiter=" ")
        listCsvReaders.append(csvReader)

    # Start reading files
    filesRead = 0
    decisions = []
    sumSetsGets = []
    for logfile in listCsvReaders:
        decisionReplica = []
        prevState = 3.650000
        numLine = 0
        setCmds = 0
        getCmds = 0
        for lineList in logfile:
            # Logic
            # Ignore metadata 
            numLine += 1
            if len(lineList) <= 1: continue    # Blank line [] or ['OK']
            if lineList[3] == "hello" or lineList[3] == "ping": continue
            # If operation is GET (set prev state in decision array for this replica)
            if lineList[3] == "get":
                decisionReplica.append(prevState)
                getCmds += 1
            # elif operation is SET (set new state in decision array for this replica)
            elif lineList[3] == "set":
                prevState = lineList[5]     # update previous state with new state
                decisionReplica.append(prevState)
                setCmds += 1
            else:
                # shoudn't happen: panic and exit
                print("Error: Operation not recognized: Op# " + str(numLine) + lineList)
                exit(1)
        # Read file done
        decisions.append(decisionReplica)
        # insert setCmds and getCmds in sumSetsGets as tuplas
        sumSetsGets.append((setCmds, getCmds))
        # Close current file and go for next one
        filesObjects[filesRead].close()
        filesRead += 1
    # print summary results
    print("Total read files: " + str(filesRead))
    # return results
    return decisions, sumSetsGets

'''
printSummaryResults: print summary results of log analysis
'''
def printSummaryResults(decisions, summary):
    print("-- Summary Results --")
    for index, replica in enumerate(decisions):
        # print index of iteration
        print('Decisions Replica # {}'.format(index))
        print(replica)
    print("Sets and Gets Commands:")
    print(summary)
    return


'''
checkConsistency: verify consistency logs finding differences
output: #inconsistencies
'''
def checkConsistency(decisions):
    # Check consistency of length of each replica
    lenArr = len(decisions[0])
    for i in range(len(decisions)):
        if len(decisions[i]) != lenArr:
            print("Error: Replica " + str(i) + " has different length")
            exit(1)
    # compare each value of each array
    countDiff = 0
    for i in range(lenArr):
        curState = decisions[0][i]
        for j in range(1, len(decisions)):
            if curState != decisions[j][i]:
                countDiff += 1
                print("Inconsistencia #" + str(countDiff) + ": Replicas have different value in #operation " + str(i))
                for k in range(len(decisions)):
                    print("Replica #" + str(k) + " : " + str(decisions[k][i]))
                break
    print("Total Inconsistencias: " + str(countDiff))
    return countDiff


'''
plotLogsReplica(): plot state of each replica in one graph
'''
def plotStateReplica(decisions):
    # Generate array of float values for each replica
    stateReplicas = []
    operationsReplicas = []
    for replica in decisions:
        stateReplica = [float(i) for i in replica]
        listOperations = list(range(len(replica)))
        stateReplicas.append(stateReplica)
        operationsReplicas.append(listOperations)

    # Add offset to each replica
    offset = True
    stateReplicasOffset = []
    myoffset = 0
    for stateReplica in stateReplicas:
        stateReplicasOffset.append([state + myoffset for state in stateReplica])
        if offset: myoffset += 0.0006

    # Plot
    # x: Operation number or Unit work ~ state (We can think this like 'time')
    # y: Value of each replica
    mycolors = ['red', 'green', 'blue', 'cyan', 'magenta' ,'yellow', 'black', 'orange', 'purple', 'pink', 'brown', 'gray']
    mymarkers = ['d', 'x', '+', '^', '>', 's', 'o', 'v', '<', 'p', '*', 'h']
    for index, replica in enumerate(stateReplicasOffset):
        plt.scatter(operationsReplicas[index], replica, color=mycolors[index], marker=mymarkers[index], label='Replica ' + str(index))
        plt.plot(operationsReplicas[index], replica, color=mycolors[index])
        # plt.semilogx(operationsReplicas[index], replica)
        # plt.semilogy(operationsReplicas[index], replica)
        # plt.gca().yaxis.set_major_formatter(LogFormatter(base=2))

    
    # Customize Plot
    plt.xlabel('Operation number')
    plt.ylabel('USD-PEN value')
    plt.title('Consistency between replicas')
    plt.legend()

    # Apply log scale to the x-axis
    # plt.xscale('log')
    # plt.xscale('symlog', linthresh=1)
    # Show plot
    plt.show()

'''
plotInconsistencies(): plot inconsistencies between replicas
Input: listInconsistencies: is a list of objects where each object is a dictionary with inconsistencies
'''
def plotInconsistencies(listInconsistencies):
    print('Plotting Inconsistencies')
    # Set the width of each bar
    barWidth = 0.35

    requestsWorkload = []  # x axis
    srInconsistencies = []  # bars in y axis
    crInconsistencies = []  # bars in y axis
    for workLoad in listInconsistencies:
        print(workLoad)
        requestsWorkload.append(workLoad['numrequests'])
        srInconsistencies.append(workLoad['inconsistencies'][0])
        crInconsistencies.append(workLoad['inconsistencies'][1])
    
    # Set the x positions of the bars
    res1_x = [x for x in range(len(requestsWorkload))]
    res2_x = [x + barWidth for x in res1_x]

    # Create the plot
    plt.bar(res1_x, srInconsistencies, color='blue', width=barWidth, edgecolor='white', label='No Rabia')
    plt.bar(res2_x, [x + 1 for x in crInconsistencies], color='green', width=barWidth, edgecolor='white', label='Using Rabia')

    # Add text labels on top of each bar
    for i, v1, v2 in zip(res1_x, srInconsistencies, crInconsistencies):
        plt.text(i, v1+0.5, str(v1), ha='center')
        plt.text(i+barWidth, v2+1, str(v2), ha='center')

    # Add xticks on the middle of the group bars
    plt.xlabel('Amount of Concurrent Requests')
    plt.ylabel('Amount of Inconsistencies')
    plt.xticks([r + barWidth / 2 for r in range(len(requestsWorkload))], requestsWorkload)

    # Add a legend
    plt.legend()

    # Show the plot
    plt.show()

    return


def mapLogFiles(isRabiaWorkload, workload_dir):
    # Samples log files
    # Sin Rabia Logs
    # srLogFile50_1 = "logs/sinrabia/t_sample_50_2c/redissvr1.log"
    # srLogFile50_2 = "logs/sinrabia/t_sample_50_2c/redissvr2.log"
    # srLogFile50_3 = "logs/sinrabia/t_sample_50_2c/redissvr3.log"
    # Con Rabia Logs
    # crLogFile50_1 = "logs/rabia/t_sample_50/rabiasvr1.log"
    # crLogFile50_2 = "logs/rabia/t_sample_50/rabiasvr2.log"
    # crLogFile50_3 = "logs/rabia/t_sample_50/rabiasvr3.log"
    # Map log files
    if isRabiaWorkload:
        logFile1 = RABIA_LOGS_DIR + workload_dir + "/rabiasvr1.log"
        logFile2 = RABIA_LOGS_DIR + workload_dir + "/rabiasvr2.log"
        logFile3 = RABIA_LOGS_DIR + workload_dir + "/rabiasvr3.log"
    else:
        logFile1 = REDIS_LOGS_DIR + workload_dir + "/redissvr1.log"
        logFile2 = REDIS_LOGS_DIR + workload_dir + "/redissvr2.log"
        logFile3 = REDIS_LOGS_DIR + workload_dir + "/redissvr3.log"
    return [logFile1, logFile2, logFile3]


def getPlotInconsistencies():
    ### Count inconsistencies for each technique ###
    listInconsistencies = []
    # Workload 50
    # Sin Rabia analysis
    srListFiles = mapLogFiles(False, "t_sample_50_2c")
    decisions, summary = readLogFiles(srListFiles)
    srTotalInconsistencies = checkConsistency(decisions)
    # Con Rabia analysis
    crListFiles = mapLogFiles(True, "t_sample_50")
    decisions, summary = readLogFiles(crListFiles)
    crTotalInconsistencies = checkConsistency(decisions)
    # Append results of workload 50
    listInconsistencies.append({'numrequests': len(decisions[0]), 'inconsistencies': (srTotalInconsistencies, crTotalInconsistencies)})

    # Workload 500
    # Sin Rabia analysis
    srListFiles = mapLogFiles(False, "t6_500")
    decisions, summary = readLogFiles(srListFiles)
    srTotalInconsistencies = checkConsistency(decisions)
    # Con Rabia analysis
    crListFiles = mapLogFiles(True, "t_sample_500")
    decisions, summary = readLogFiles(crListFiles)
    crTotalInconsistencies = checkConsistency(decisions)
    # Append results of workload 500
    listInconsistencies.append({'numrequests': len(decisions[0]), 'inconsistencies': (srTotalInconsistencies, crTotalInconsistencies)})
    
    # Plot results
    print("listInconsistencies: ")
    print(listInconsistencies)
    plotInconsistencies(listInconsistencies)


def main():
    
    '''
    # Make list of log files
    srListFiles = [srLogFile1, srLogFile2, srLogFile3]
    # Read log files
    decisions, summary = readLogFiles(srListFiles)
    #printSummaryResults(decisions, summary)
    srTotalInc = checkConsistency(decisions)
    plotStateReplica(decisions)
    '''
    getPlotInconsistencies()
    print("done...bye!")


if __name__ == "__main__":
    main()
