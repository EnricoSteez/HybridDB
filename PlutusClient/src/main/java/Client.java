import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.Server;
import io.grpc.ServerBuilder;
import io.grpc.stub.StreamObserver;

import java.io.IOException;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.logging.Logger;
import java.util.stream.Collectors;

public class Client {
    private static Map<String, Item> items;
    private final InitializationGrpc.InitializationBlockingStub initializationBlockingStub;
    private final int localPort;
    private static final long initTime = System.currentTimeMillis();
    private Server server;
    private static final Logger logger = Logger.getLogger(Client.class.getName());



    public Client (ManagedChannel channel, int localPort){
        initializationBlockingStub = InitializationGrpc.newBlockingStub(channel);
        items = new HashMap<>();
        this.localPort = localPort;
    }

    private void start() throws IOException {
        /* The port on which the server should run */
        int port = 50051;
        server = ServerBuilder.forPort(port)
                .addService(new Coordination())
                .build()
                .start();
        logger.info("Server started, listening on " + port);
        Runtime.getRuntime().addShutdownHook(new Thread() {
            @Override
            public void run() {
                // Use stderr here since the logger may have been reset by its JVM shutdown hook.
                System.err.println("*** shutting down gRPC server since JVM is shutting down");
                try {
                    Client.this.stop();
                } catch (InterruptedException e) {
                    e.printStackTrace(System.err);
                }
                System.err.println("*** server shut down");
            }
        });
    }

    private void stop() throws InterruptedException {
        if (server != null) {
            server.shutdown().awaitTermination(30, TimeUnit.SECONDS);
        }
    }

    /**
     * Await termination on the main thread since the grpc library uses daemon threads.
     */
    private void blockUntilShutdown() throws InterruptedException {
        if (server != null) {
            server.awaitTermination();
        }
    }


    private boolean registerClient() {
        InitializationServices.RegisterRequest request =
                null;
        try {
            request = InitializationServices.RegisterRequest
                    .newBuilder()
                    .setIp(InetAddress.getLocalHost().getHostAddress())
                    .setPort(localPort)
                    .build();
        } catch (UnknownHostException e) {
            e.printStackTrace();
        }
        InitializationServices.RegisterReply reply = initializationBlockingStub.registerClient(request);
        return reply.getOk();
    }

    public static void main (String[] args)  throws IOException, InterruptedException{
        int localPort = 50099;
        String serverIP = "localhost";
        int serverPort = 50051;
        if(args.length != 0 && args.length != 3) {
            System.err.println("Usage: LocalPort ServerIP ServerPort");
            System.exit(1);
        }

        if(args.length==3) {
            if (!isIp(args[1])) throw new IllegalArgumentException("IP is not valid");
            serverIP = args[1];
            try {
                localPort = Integer.parseInt(args[0]);
                serverPort = Integer.parseInt(args[2]);
            } catch (NumberFormatException e) {
                throw new IllegalArgumentException(e);
            }
        }
        String target = serverIP + ":" + serverPort;
        ManagedChannel channel = ManagedChannelBuilder
                .forTarget(target)
                .usePlaintext()
                .build();
        try {
            Client client=new Client(channel, localPort);
            boolean ok = client.registerClient();
            if(!ok) throw new RuntimeException("Cannot register client");
            new Thread(new ClientBehaviour()).start();
            client.start();
            client.blockUntilShutdown();

            //TODO check how the thread can access ITEMS
            //TODO check if it can be run on a separate window

        } catch(RuntimeException e) {
            e.printStackTrace();
        }
        finally {
            // ManagedChannels use resources like threads and TCP connections. To prevent leaking these
            // resources the channel should be shut down when it will no longer be used. If it may be used
            // again leave it running.
            try {
                channel.shutdownNow().awaitTermination(5, TimeUnit.SECONDS);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }

    private static boolean isIp (String ip) {
        // Check if the string is not null
        if (ip == null)
            return false;

        // Get the parts of the ip
        String[] parts = ip.split("\\.");

        if (parts.length != 4)
            return false;

        for (String s : parts) {
            try {
                int value = Integer.parseInt(s);

                // out of range
                if (value <= 0 || value >= 255) {
                    return false;
                }
            } catch (Exception e) {
                return false;
            }
        }
        return true;
    }

    static class Coordination extends CoordinationMethodsGrpc.CoordinationMethodsImplBase {
        @Override
        public void gatherThroughputs (CoordinationServices.GatherThroughputsRequest request, StreamObserver<CoordinationServices.GatherThroughputsReply> responseObserver) {
//            super.gatherThroughputs(request, responseObserver);
            long evaluationPeriod = System.currentTimeMillis() - initTime;
            // FOR EVERY ITEM, MAP IT TO a Throughput(protobuf) object with same id and value: (reads+writes)/evalTime
            CoordinationServices.GatherThroughputsReply reply =
                    CoordinationServices.GatherThroughputsReply.newBuilder()
                            .addAllThroughputs(
                                    items
                                            .values()
                                            .stream()
                                            .map(item -> CoordinationServices.Throughput.newBuilder()
                                                    .setId(item.getId())
                                                    .setThroughput((item.getCountReads()+ item.getCountWrites())/evaluationPeriod)
                                                    .build())
                                            .collect(Collectors.toCollection(ArrayList::new)))
                            .build();
            responseObserver.onNext(reply);
            responseObserver.onCompleted();
        }

        @Override
        public void freeze (CoordinationServices.FreezeRequest request, StreamObserver<CoordinationServices.FreezeReply> responseObserver) {
//            super.freeze(request, responseObserver);
            List<String> keys = request.getKeysList();
            List<String> notFound = new ArrayList<>();
            for( String key : keys) {
                if(!items.containsKey(key))
                    notFound.add(key);
                items.get(key).freeze();
            }

            CoordinationServices.FreezeReply reply = CoordinationServices.FreezeReply.newBuilder()
                    .addAllNotFound(notFound)
                    .build();
            responseObserver.onNext(reply);
            responseObserver.onCompleted();
        }

        @Override
        public void unfreeze (CoordinationServices.UnfreezeRequest request, StreamObserver<CoordinationServices.UnfreezeReply> responseObserver) {
//            super.unfreeze(request, responseObserver);
            List<CoordinationServices.ItemPlacement> placements = request.getNewPlacementList();
            for(CoordinationServices.ItemPlacement placement : placements) {
                String id = placement.getId();
                int whichBackend = placement.getPlacement();
                items.get(id).setPlacement(whichBackend);
            }
        }
    }

}
