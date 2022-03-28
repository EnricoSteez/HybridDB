import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.stub.StreamObserver;

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;

public class Client {
    private Map<String, Item> items;
    private final CoordinationMethodsGrpc.CoordinationMethodsStub asyncStub;
    private final InitializationGrpc.InitializationBlockingStub initializationBlockingStub;
    private final int localPort;

    public Client (ManagedChannel channel, int localPort){
        asyncStub = CoordinationMethodsGrpc.newStub(channel);
        initializationBlockingStub = InitializationGrpc.newBlockingStub(channel);
        items = new HashMap<>();
        this.localPort = localPort;
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

    public static void main (String[] args) {
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


            //TODO implement more things here

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
        public void freezeProposal (CoordinationServices.FreezeRequest request, StreamObserver<CoordinationServices.FreezeReply> responseObserver) {
            super.freezeProposal(request, responseObserver);
        }

        @Override
        public void freezeOrder (CoordinationServices.FreezeOrderRequest request, StreamObserver<CoordinationServices.FreezeOrderReply> responseObserver) {
            super.freezeOrder(request, responseObserver);
        }

        @Override
        public void unfreeze (CoordinationServices.UnfreezeRequest request, StreamObserver<CoordinationServices.UnfreezeReply> responseObserver) {
            super.unfreeze(request, responseObserver);
        }
    }

}
