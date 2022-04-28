import io.grpc.*;
import io.grpc.stub.StreamObserver;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.Random;
import java.util.concurrent.TimeUnit;
import java.util.logging.Logger;

public class PlutusServer {

    private static final Logger logger = Logger.getLogger(PlutusServer.class.getName());
    private Server server;
    // k->IP:port, v->stub
    private static Map<String, CoordinationMethodsGrpc.CoordinationMethodsStub> clients;
    private static Map<String, Integer> currentPlacement;
    private static DatabaseController databaseController;
    private static final int N = 1000;
    //TODO GRAB N ON THE FLY: COUNT ITEMS FROM BOTH DATABASES AND SUM


    public PlutusServer() {
        clients = new HashMap<>();
        //Initialize placement
        currentPlacement = new HashMap<>();
        Random r = new Random();
        byte[] b = new byte[10];
        //TODO REMOVE THIS MOCK INITIALIZATION AND RETRIEVE STUFF ON THE FLY FROM THE BACKENDS
        for(int i=0;i<N;i++){
            r.nextBytes(b);
            //all items on Dynamo initially
            currentPlacement.put(new String(b, StandardCharsets.UTF_8),0);
        }
        databaseController = new DatabaseController();
    }

    private void start() throws IOException {
        /* The port on which the server should run */
        int port = 50051;
        server = ServerBuilder.forPort(port)
                .addService(new Initialization())
                .build()
                .start();
        logger.info("Server started, listening on " + port);
        Runtime.getRuntime().addShutdownHook(new Thread() {
            @Override
            public void run() {
                // Use stderr here since the logger may have been reset by its JVM shutdown hook.
                System.err.println("*** shutting down gRPC server since JVM is shutting down");
                try {
                    PlutusServer.this.stop();
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

    /**
     * Main launches the server from the command line.
     */
    public static void main(String[] args) throws IOException, InterruptedException {
        final PlutusServer server = new PlutusServer();
        server.start();
        server.blockUntilShutdown();

        //TODO LAUNCH THIS PERIODICALLY, INSTEAD of only once
        System.out.println("Optimization should start hereafter... ");
        new Thread(new Optimizer(clients,currentPlacement,databaseController)).start();
    }

    static class Initialization extends InitializationGrpc.InitializationImplBase {
        @Override
        public void registerClient (ClientToPlutusInit.RegisterRequest request, StreamObserver<ClientToPlutusInit.RegisterReply> responseObserver) {
            String ip = request.getIp();
            int port = request.getPort();
            String target = ip + ":" + port;
            System.out.println("Registering client :"+target);

            ManagedChannel channel = ManagedChannelBuilder
                    .forTarget(target)
                    .usePlaintext()
                    .build();
            clients.put(target,CoordinationMethodsGrpc.newStub(channel));
//            new Thread(new UserInteraction()).start();
            ClientToPlutusInit.RegisterReply reply = ClientToPlutusInit.RegisterReply.newBuilder().setOk(true).build();
            responseObserver.onNext(reply);
            responseObserver.onCompleted();
        }
    }
}

