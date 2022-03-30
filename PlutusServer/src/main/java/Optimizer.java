import java.util.Map;

public class Optimizer implements Runnable{

    private final Map<String, CoordinationMethodsGrpc.CoordinationMethodsStub> clients;

    public Optimizer (Map<String, CoordinationMethodsGrpc.CoordinationMethodsStub> clients) {
        this.clients = clients;
    }

    @Override
    public void run () {
        clients.forEach((target, stub) -> {
            CoordinationServices.GatherThroughputsRequest req =
                    CoordinationServices.GatherThroughputsRequest
                            .newBuilder()
                            .build();
            //TODO: Check how to use StreamObserver for async stub
//            stub.gatherThroughputs(req);
        });
    }
}
