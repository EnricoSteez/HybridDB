import io.grpc.stub.StreamObserver;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

public record Optimizer(
        Map<String, CoordinationMethodsGrpc.CoordinationMethodsStub> clients) implements Runnable {

    private static Map<String, Long> throughputs;

    public Optimizer (Map<String, CoordinationMethodsGrpc.CoordinationMethodsStub> clients) {
        this.clients = clients;
        throughputs = new ConcurrentHashMap<>();
    }

    @Override
    public void run () {
        clients.forEach((target, stub) -> {
            CoordinationServices.GatherThroughputsRequest req =
                    CoordinationServices.GatherThroughputsRequest
                            .newBuilder()
                            .build();
            // DEFINITION OF THE BEHAVIOUR WHEN CLIENT RESPONSES WILL ARRIVE
            StreamObserver<CoordinationServices.GatherThroughputsReply> gatherThroughputsStreamObserver = new StreamObserver<CoordinationServices.GatherThroughputsReply>() {
                @Override
                public void onNext (CoordinationServices.GatherThroughputsReply gatherThroughputsReply) {
                    System.out.println("Reply from client.");
                    gatherThroughputsReply.getThroughputsList().forEach((throughput -> {
                        String id = throughput.getId();
                        Long tp = throughput.getThroughput();
                        throughputs.put(id, throughputs.getOrDefault(id, 0L) + tp);
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
            List<String> itemsToMove = optimizePlacement(throughputs);

            StreamObserver<CoordinationServices.FreezeReply> freezeReplyStreamObserver = new StreamObserver<CoordinationServices.FreezeReply>() {
                @Override
                public void onNext (CoordinationServices.FreezeReply freezeReply) {
                    freezeReply.getNotFoundList().forEach(id -> {
                        throughputs.remove(id);
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
            CoordinationServices.FreezeRequest freezeRequest = CoordinationServices.FreezeRequest.newBuilder()
                    .addAllKeys(throughputs.keySet())
                    .build();

            //TELL CLIENTS TO FREEZE CRITICAL ITEMS TO BE MOVED
            stub.freeze(freezeRequest,freezeReplyStreamObserver);

            //AT THIS POINT THE CLIENTS SHOULD QUEUE ALL REQUESTS TARGETING KEYS IN THE FREEZE SET

            Map<String,Integer> newPlacement = moveData(throughputs.keySet());

            CoordinationServices.UnfreezeRequest unfreezeRequest = CoordinationServices.UnfreezeRequest.newBuilder()
                    .addAllNewPlacement(newPlacement
                            .entrySet()
                            .stream()
                            .sequential()
                            .map(item -> CoordinationServices.ItemPlacement.newBuilder()
                                    .setId(item.getKey())
                                    .setPlacement(item.getValue())
                                    .build())
                            .collect(Collectors.toCollection(ArrayList::new)))
                    .build();

            StreamObserver<CoordinationServices.UnfreezeReply> unfreezeReplyStreamObserver = new StreamObserver<CoordinationServices.UnfreezeReply>() {
                @Override
                public void onNext (CoordinationServices.UnfreezeReply unfreezeReply) {
                    if(unfreezeReply.getDone())
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
                    System.out.println("All client unfreezed the items. Optimization complete");
                }
            };

            stub.unfreeze(unfreezeRequest,unfreezeReplyStreamObserver);

            //END OF OPTMIZATION ROUTINE
        });
    }

    private Map<String, Integer> moveData (Set<String> keySet) {
        Map<String,Integer> newPlacement = new HashMap<>();
        //TODO IMPLEMENT DATA TRANSFER
        return newPlacement;
    }

    private List<String> optimizePlacement (Map<String, Long> throughputs) {
        List<String> itemsToMove = new ArrayList<>();

        //TODO CALL PYTHON OPTIMIZER

        return itemsToMove;
    }
}
