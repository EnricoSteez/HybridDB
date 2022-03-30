import io.grpc.*;
import io.grpc.stub.StreamObserver;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.logging.Logger;

public class PlutusServer {

    private static final Logger logger = Logger.getLogger(PlutusServer.class.getName());
    private Server server;
    // k->IP:port, v->stub
    private static Map<String, CoordinationMethodsGrpc.CoordinationMethodsStub> clients;

    public PlutusServer() {
        clients = new HashMap<>();
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

        //TODO figure out how the thread can access the list of clients
        new Thread(new Optimizer(clients)).start();
    }

    static class Initialization extends InitializationGrpc.InitializationImplBase {
        @Override
        public void registerClient (InitializationServices.RegisterRequest request, StreamObserver<InitializationServices.RegisterReply> responseObserver) {
//            super.registerClient(request, responseObserver);
            String ip = request.getIp();
            int port = request.getPort();
            String target = ip + ":" + port;
            ManagedChannel channel = ManagedChannelBuilder
                    .forTarget(target)
                    .usePlaintext()
                    .build();
            clients.put(target,CoordinationMethodsGrpc.newStub(channel));
        }
    }
}

