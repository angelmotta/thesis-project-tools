import csv
import itertools
import matplotlib.pyplot as plt

zip_longest = itertools.zip_longest

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
output: list of operations executed by each replica
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
        prevState = 0
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
def checkConsistency():
    return


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
    
    # Customize Plot
    plt.xlabel('Operation number')
    plt.ylabel('USD-PEN value')
    plt.title('Consistency between replicas')
    plt.legend()

    # Show plot
    plt.show()



def main():
    logfile1 = "logs/rabia/t_sample_50/rabiasvr1log.txt"
    logfile2 = "logs/rabia/t_sample_50/rabiasvr2log.txt"
    logfile3 = "logs/rabia/t_sample_50/rabiasvr3log.txt"
    #readLogFiles(logfile1, logfile2, logfile3)
    listFiles = [logfile1, logfile2, logfile3]
    decisions, summary = readLogFiles(listFiles)
    printSummaryResults(decisions, summary)
    #checkConsistency(decisions)
    plotStateReplica(decisions)
    print("done...bye!")


if __name__ == "__main__":
    main()
