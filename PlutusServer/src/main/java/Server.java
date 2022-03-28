import io.grpc.stub.StreamObserver;

public class Server {


    static class Initialization extends InitializationGrpc.InitializationImplBase {
        @Override
        public void registerClient (InitializationServices.RegisterRequest request, StreamObserver<InitializationServices.RegisterReply> responseObserver) {
//            super.registerClient(request, responseObserver);

        }
    }
}

