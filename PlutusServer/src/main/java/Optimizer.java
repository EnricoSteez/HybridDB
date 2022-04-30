import io.grpc.stub.StreamObserver;

import java.io.*;
import java.util.*;
import java.util.stream.Collectors;

public record Optimizer(
        Map<String, CoordinationMethodsGrpc.CoordinationMethodsStub> clients,
        Map<String, Integer> currentPlacement,
        DatabaseController controller) implements Runnable {

    private static SortedMap<String, Long> throughputsRead;
    private static SortedMap<String, Long> throughputsWrite;


    public Optimizer (Map<String, CoordinationMethodsGrpc.CoordinationMethodsStub> clients, Map<String, Integer> currentPlacement, DatabaseController controller) {
        this.clients = clients;
        // SORTED BY KEY FOR BETTER HANDLING.
        // THREADSAFE FOR THE COLLECTION PROCEDURE
        throughputsRead = Collections.synchronizedSortedMap(new TreeMap<>());
        throughputsWrite = Collections.synchronizedSortedMap(new TreeMap<>());
        this.currentPlacement = currentPlacement;
        this.controller = controller;
    }

    @Override
    public void run () {
        throughputsRead.clear();
        throughputsWrite.clear();
        clients.forEach((target, stub) -> {
            PlutusToClients.GatherThroughputsRequest req =
                    PlutusToClients.GatherThroughputsRequest
                            .newBuilder()
                            .build();
            // DEFINITION OF THE BEHAVIOUR WHEN CLIENT RESPONSES WILL ARRIVE
            StreamObserver<PlutusToClients.GatherThroughputsReply> gatherThroughputsStreamObserver = new StreamObserver<>() {
                @Override
                public void onNext (PlutusToClients.GatherThroughputsReply gatherThroughputsReply) {
                    System.out.println("Reply from client.");
                    gatherThroughputsReply.getThroughputsReadList().forEach((throughput -> {
                        String id = throughput.getId();
                        Long tp = throughput.getThroughput();
                        throughputsRead.put(id, throughputsRead.getOrDefault(id, 0L) + tp);
                    }));
                    gatherThroughputsReply.getThroughputsWriteList().forEach((throughput -> {
                        String id = throughput.getId();
                        Long tp = throughput.getThroughput();
                        throughputsWrite.put(id, throughputsWrite.getOrDefault(id, 0L) + tp);
                    }));
                }

                @Override
                public void onError (Throwable throwable) {

                }

                @Override
                public void onCompleted () {
                    System.out.println("Finished merging throughputs");
                }
            };
            // ACTUAL CALL TO CLIENTS ASKING FOR THROUGHPUTS
            stub.gatherThroughputs(req, gatherThroughputsStreamObserver);

            //here all throughputs should be gathered

            //RUN OPTIMIZER
            Map<String, Integer> newPlacement = null;
            try {
                newPlacement = optimizePlacement(throughputsRead, throughputsWrite);
            } catch (IOException | InterruptedException e) {
                e.printStackTrace();
            }
            Map<String, Integer> itemsToMove = comparePlacements(currentPlacement, newPlacement);

            StreamObserver<PlutusToClients.FreezeReply> freezeReplyStreamObserver = new StreamObserver<>() {
                @Override
                public void onNext (PlutusToClients.FreezeReply freezeReply) {
                    freezeReply.getNotFoundList().forEach(id -> {
                        throughputsRead.remove(id);
                        System.out.println("Removed item " + id + " since it has been deleted from the DB in the meantime...");
                    });
                }

                @Override
                public void onError (Throwable throwable) {

                }

                @Override
                public void onCompleted () {
                    System.out.println("Finished Freezing items, now I'll replace items between databases!");
                }
            };
            PlutusToClients.FreezeRequest freezeRequest = PlutusToClients.FreezeRequest.newBuilder()
                    .addAllKeys(itemsToMove.keySet())
                    .build();

            //TELL CLIENTS TO FREEZE CRITICAL ITEMS TO BE MOVED
            stub.freeze(freezeRequest, freezeReplyStreamObserver);

            //AT THIS POINT THE CLIENTS SHOULD QUEUE ALL REQUESTS TARGETING KEYS IN THE FREEZE SET

            Set<String> fails = moveData(itemsToMove);
            if (!fails.isEmpty()) {
                //TODO
            }

            PlutusToClients.UnfreezeRequest unfreezeRequest = PlutusToClients.UnfreezeRequest.newBuilder()
                    .addAllNewPlacement(newPlacement
                            .entrySet()
                            .stream()
                            .sequential()
                            .map(item -> PlutusToClients.ItemPlacement.newBuilder()
                                    .setId(item.getKey())
                                    .setPlacement(item.getValue())
                                    .build())
                            .collect(Collectors.toCollection(ArrayList::new)))
                    .build();

            StreamObserver<PlutusToClients.UnfreezeReply> unfreezeReplyStreamObserver = new StreamObserver<PlutusToClients.UnfreezeReply>() {
                @Override
                public void onNext (PlutusToClients.UnfreezeReply unfreezeReply) {
                    if (unfreezeReply.getDone())
                        System.out.println("Client unfroze set");
                    else {
                        System.out.println("One client raised an error. Abort");
                        this.onError(new RuntimeException("Error while unfreezing"));
                    }
                }

                @Override
                public void onError (Throwable throwable) {
                    throwable.printStackTrace();
                }

                @Override
                public void onCompleted () {
                    System.out.println("All client unfroze the items. Optimization complete");
                }
            };

            stub.unfreeze(unfreezeRequest, unfreezeReplyStreamObserver);

            //END OF OPTIMIZATION ROUTINE
        });
    }

    private Map<String, Integer> comparePlacements (Map<String, Integer> currentPlacement, Map<String, Integer> newPlacement) {
        Map<String, Integer> itemsThatChanged = new HashMap<>();
        for (Map.Entry<String, Integer> item : currentPlacement.entrySet()) {
            if (!Objects.equals(currentPlacement.get(item.getKey()), newPlacement.get(item.getKey())))
                itemsThatChanged.put(item.getKey(), item.getValue());
        }
        return itemsThatChanged;
    }

    private Set<String> moveData (Map<String, Integer> items) {
        //TODO implement data transfer with Controller class
        return null;
    }

    private void moveItem (String key, Integer value) throws RuntimeException {
        //TODO INVOKE DATA TRANSFER ON SINGLE ITEMS (CONTROLLER)
    }

    private Map<String, Integer> optimizePlacement (Map<String, Long> throughputsRead, Map<String, Long> throughputsWrite)
            throws IOException, InterruptedException {
        Map<String, Integer> newPlacement = new HashMap<>();
        try (
                BufferedWriter writer = new BufferedWriter(new FileWriter("throughputs.txt")) ;
        ) {
            for (String tp : throughputsRead.keySet())
                writer.write(tp + " " + throughputsRead.get(tp) + " " + throughputsWrite.getOrDefault(tp, 0L));
        }
        int items = Math.max(throughputsRead.size(), throughputsWrite.size());
        System.out.println("Calling solver with " + items + " items.");
        ProcessBuilder builder = new ProcessBuilder("python3 ../../../../lp_solve_novmtype.py " + items + " java");
        builder.redirectErrorStream(true);
        Process process = builder.start();
        process.waitFor();
        try (
                InputStream inputStream = new FileInputStream("placement") ;
        ) {
            int byteRead = -1;
            while ((byteRead = inputStream.read()) != -1) {
                
            }

        } catch (IOException ex) {
            ex.printStackTrace();
        }
        //CALL PYTHON OPTIMIZER HERE
        return newPlacement;
    }
}
