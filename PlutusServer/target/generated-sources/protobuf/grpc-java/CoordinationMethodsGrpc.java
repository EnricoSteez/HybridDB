import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.43.1)",
    comments = "Source: coordination_services.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class CoordinationMethodsGrpc {

  private CoordinationMethodsGrpc() {}

  public static final String SERVICE_NAME = "CoordinationMethods";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<CoordinationServices.FreezeRequest,
      CoordinationServices.FreezeReply> getFreezeProposalMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "FreezeProposal",
      requestType = CoordinationServices.FreezeRequest.class,
      responseType = CoordinationServices.FreezeReply.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<CoordinationServices.FreezeRequest,
      CoordinationServices.FreezeReply> getFreezeProposalMethod() {
    io.grpc.MethodDescriptor<CoordinationServices.FreezeRequest, CoordinationServices.FreezeReply> getFreezeProposalMethod;
    if ((getFreezeProposalMethod = CoordinationMethodsGrpc.getFreezeProposalMethod) == null) {
      synchronized (CoordinationMethodsGrpc.class) {
        if ((getFreezeProposalMethod = CoordinationMethodsGrpc.getFreezeProposalMethod) == null) {
          CoordinationMethodsGrpc.getFreezeProposalMethod = getFreezeProposalMethod =
              io.grpc.MethodDescriptor.<CoordinationServices.FreezeRequest, CoordinationServices.FreezeReply>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "FreezeProposal"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  CoordinationServices.FreezeRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  CoordinationServices.FreezeReply.getDefaultInstance()))
              .setSchemaDescriptor(new CoordinationMethodsMethodDescriptorSupplier("FreezeProposal"))
              .build();
        }
      }
    }
    return getFreezeProposalMethod;
  }

  private static volatile io.grpc.MethodDescriptor<CoordinationServices.FreezeOrderRequest,
      CoordinationServices.FreezeOrderReply> getFreezeOrderMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "FreezeOrder",
      requestType = CoordinationServices.FreezeOrderRequest.class,
      responseType = CoordinationServices.FreezeOrderReply.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<CoordinationServices.FreezeOrderRequest,
      CoordinationServices.FreezeOrderReply> getFreezeOrderMethod() {
    io.grpc.MethodDescriptor<CoordinationServices.FreezeOrderRequest, CoordinationServices.FreezeOrderReply> getFreezeOrderMethod;
    if ((getFreezeOrderMethod = CoordinationMethodsGrpc.getFreezeOrderMethod) == null) {
      synchronized (CoordinationMethodsGrpc.class) {
        if ((getFreezeOrderMethod = CoordinationMethodsGrpc.getFreezeOrderMethod) == null) {
          CoordinationMethodsGrpc.getFreezeOrderMethod = getFreezeOrderMethod =
              io.grpc.MethodDescriptor.<CoordinationServices.FreezeOrderRequest, CoordinationServices.FreezeOrderReply>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "FreezeOrder"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  CoordinationServices.FreezeOrderRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  CoordinationServices.FreezeOrderReply.getDefaultInstance()))
              .setSchemaDescriptor(new CoordinationMethodsMethodDescriptorSupplier("FreezeOrder"))
              .build();
        }
      }
    }
    return getFreezeOrderMethod;
  }

  private static volatile io.grpc.MethodDescriptor<CoordinationServices.UnfreezeRequest,
      CoordinationServices.UnfreezeReply> getUnfreezeMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "Unfreeze",
      requestType = CoordinationServices.UnfreezeRequest.class,
      responseType = CoordinationServices.UnfreezeReply.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<CoordinationServices.UnfreezeRequest,
      CoordinationServices.UnfreezeReply> getUnfreezeMethod() {
    io.grpc.MethodDescriptor<CoordinationServices.UnfreezeRequest, CoordinationServices.UnfreezeReply> getUnfreezeMethod;
    if ((getUnfreezeMethod = CoordinationMethodsGrpc.getUnfreezeMethod) == null) {
      synchronized (CoordinationMethodsGrpc.class) {
        if ((getUnfreezeMethod = CoordinationMethodsGrpc.getUnfreezeMethod) == null) {
          CoordinationMethodsGrpc.getUnfreezeMethod = getUnfreezeMethod =
              io.grpc.MethodDescriptor.<CoordinationServices.UnfreezeRequest, CoordinationServices.UnfreezeReply>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "Unfreeze"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  CoordinationServices.UnfreezeRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  CoordinationServices.UnfreezeReply.getDefaultInstance()))
              .setSchemaDescriptor(new CoordinationMethodsMethodDescriptorSupplier("Unfreeze"))
              .build();
        }
      }
    }
    return getUnfreezeMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static CoordinationMethodsStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<CoordinationMethodsStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<CoordinationMethodsStub>() {
        @java.lang.Override
        public CoordinationMethodsStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new CoordinationMethodsStub(channel, callOptions);
        }
      };
    return CoordinationMethodsStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static CoordinationMethodsBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<CoordinationMethodsBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<CoordinationMethodsBlockingStub>() {
        @java.lang.Override
        public CoordinationMethodsBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new CoordinationMethodsBlockingStub(channel, callOptions);
        }
      };
    return CoordinationMethodsBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static CoordinationMethodsFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<CoordinationMethodsFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<CoordinationMethodsFutureStub>() {
        @java.lang.Override
        public CoordinationMethodsFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new CoordinationMethodsFutureStub(channel, callOptions);
        }
      };
    return CoordinationMethodsFutureStub.newStub(factory, channel);
  }

  /**
   */
  public static abstract class CoordinationMethodsImplBase implements io.grpc.BindableService {

    /**
     */
    public void freezeProposal(CoordinationServices.FreezeRequest request,
        io.grpc.stub.StreamObserver<CoordinationServices.FreezeReply> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getFreezeProposalMethod(), responseObserver);
    }

    /**
     */
    public void freezeOrder(CoordinationServices.FreezeOrderRequest request,
        io.grpc.stub.StreamObserver<CoordinationServices.FreezeOrderReply> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getFreezeOrderMethod(), responseObserver);
    }

    /**
     */
    public void unfreeze(CoordinationServices.UnfreezeRequest request,
        io.grpc.stub.StreamObserver<CoordinationServices.UnfreezeReply> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getUnfreezeMethod(), responseObserver);
    }

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return io.grpc.ServerServiceDefinition.builder(getServiceDescriptor())
          .addMethod(
            getFreezeProposalMethod(),
            io.grpc.stub.ServerCalls.asyncUnaryCall(
              new MethodHandlers<
                CoordinationServices.FreezeRequest,
                CoordinationServices.FreezeReply>(
                  this, METHODID_FREEZE_PROPOSAL)))
          .addMethod(
            getFreezeOrderMethod(),
            io.grpc.stub.ServerCalls.asyncUnaryCall(
              new MethodHandlers<
                CoordinationServices.FreezeOrderRequest,
                CoordinationServices.FreezeOrderReply>(
                  this, METHODID_FREEZE_ORDER)))
          .addMethod(
            getUnfreezeMethod(),
            io.grpc.stub.ServerCalls.asyncUnaryCall(
              new MethodHandlers<
                CoordinationServices.UnfreezeRequest,
                CoordinationServices.UnfreezeReply>(
                  this, METHODID_UNFREEZE)))
          .build();
    }
  }

  /**
   */
  public static final class CoordinationMethodsStub extends io.grpc.stub.AbstractAsyncStub<CoordinationMethodsStub> {
    private CoordinationMethodsStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected CoordinationMethodsStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new CoordinationMethodsStub(channel, callOptions);
    }

    /**
     */
    public void freezeProposal(CoordinationServices.FreezeRequest request,
        io.grpc.stub.StreamObserver<CoordinationServices.FreezeReply> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getFreezeProposalMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void freezeOrder(CoordinationServices.FreezeOrderRequest request,
        io.grpc.stub.StreamObserver<CoordinationServices.FreezeOrderReply> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getFreezeOrderMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void unfreeze(CoordinationServices.UnfreezeRequest request,
        io.grpc.stub.StreamObserver<CoordinationServices.UnfreezeReply> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getUnfreezeMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   */
  public static final class CoordinationMethodsBlockingStub extends io.grpc.stub.AbstractBlockingStub<CoordinationMethodsBlockingStub> {
    private CoordinationMethodsBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected CoordinationMethodsBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new CoordinationMethodsBlockingStub(channel, callOptions);
    }

    /**
     */
    public CoordinationServices.FreezeReply freezeProposal(CoordinationServices.FreezeRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getFreezeProposalMethod(), getCallOptions(), request);
    }

    /**
     */
    public CoordinationServices.FreezeOrderReply freezeOrder(CoordinationServices.FreezeOrderRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getFreezeOrderMethod(), getCallOptions(), request);
    }

    /**
     */
    public CoordinationServices.UnfreezeReply unfreeze(CoordinationServices.UnfreezeRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getUnfreezeMethod(), getCallOptions(), request);
    }
  }

  /**
   */
  public static final class CoordinationMethodsFutureStub extends io.grpc.stub.AbstractFutureStub<CoordinationMethodsFutureStub> {
    private CoordinationMethodsFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected CoordinationMethodsFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new CoordinationMethodsFutureStub(channel, callOptions);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<CoordinationServices.FreezeReply> freezeProposal(
        CoordinationServices.FreezeRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getFreezeProposalMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<CoordinationServices.FreezeOrderReply> freezeOrder(
        CoordinationServices.FreezeOrderRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getFreezeOrderMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<CoordinationServices.UnfreezeReply> unfreeze(
        CoordinationServices.UnfreezeRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getUnfreezeMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_FREEZE_PROPOSAL = 0;
  private static final int METHODID_FREEZE_ORDER = 1;
  private static final int METHODID_UNFREEZE = 2;

  private static final class MethodHandlers<Req, Resp> implements
      io.grpc.stub.ServerCalls.UnaryMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ServerStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ClientStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.BidiStreamingMethod<Req, Resp> {
    private final CoordinationMethodsImplBase serviceImpl;
    private final int methodId;

    MethodHandlers(CoordinationMethodsImplBase serviceImpl, int methodId) {
      this.serviceImpl = serviceImpl;
      this.methodId = methodId;
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public void invoke(Req request, io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        case METHODID_FREEZE_PROPOSAL:
          serviceImpl.freezeProposal((CoordinationServices.FreezeRequest) request,
              (io.grpc.stub.StreamObserver<CoordinationServices.FreezeReply>) responseObserver);
          break;
        case METHODID_FREEZE_ORDER:
          serviceImpl.freezeOrder((CoordinationServices.FreezeOrderRequest) request,
              (io.grpc.stub.StreamObserver<CoordinationServices.FreezeOrderReply>) responseObserver);
          break;
        case METHODID_UNFREEZE:
          serviceImpl.unfreeze((CoordinationServices.UnfreezeRequest) request,
              (io.grpc.stub.StreamObserver<CoordinationServices.UnfreezeReply>) responseObserver);
          break;
        default:
          throw new AssertionError();
      }
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public io.grpc.stub.StreamObserver<Req> invoke(
        io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        default:
          throw new AssertionError();
      }
    }
  }

  private static abstract class CoordinationMethodsBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    CoordinationMethodsBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return CoordinationServices.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("CoordinationMethods");
    }
  }

  private static final class CoordinationMethodsFileDescriptorSupplier
      extends CoordinationMethodsBaseDescriptorSupplier {
    CoordinationMethodsFileDescriptorSupplier() {}
  }

  private static final class CoordinationMethodsMethodDescriptorSupplier
      extends CoordinationMethodsBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final String methodName;

    CoordinationMethodsMethodDescriptorSupplier(String methodName) {
      this.methodName = methodName;
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.MethodDescriptor getMethodDescriptor() {
      return getServiceDescriptor().findMethodByName(methodName);
    }
  }

  private static volatile io.grpc.ServiceDescriptor serviceDescriptor;

  public static io.grpc.ServiceDescriptor getServiceDescriptor() {
    io.grpc.ServiceDescriptor result = serviceDescriptor;
    if (result == null) {
      synchronized (CoordinationMethodsGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new CoordinationMethodsFileDescriptorSupplier())
              .addMethod(getFreezeProposalMethod())
              .addMethod(getFreezeOrderMethod())
              .addMethod(getUnfreezeMethod())
              .build();
        }
      }
    }
    return result;
  }
}
