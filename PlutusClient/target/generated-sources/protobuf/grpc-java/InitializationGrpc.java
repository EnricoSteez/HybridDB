import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.43.1)",
    comments = "Source: initialization_services.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class InitializationGrpc {

  private InitializationGrpc() {}

  public static final String SERVICE_NAME = "Initialization";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<InitializationServices.RegisterRequest,
      InitializationServices.RegisterReply> getRegisterClientMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "RegisterClient",
      requestType = InitializationServices.RegisterRequest.class,
      responseType = InitializationServices.RegisterReply.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<InitializationServices.RegisterRequest,
      InitializationServices.RegisterReply> getRegisterClientMethod() {
    io.grpc.MethodDescriptor<InitializationServices.RegisterRequest, InitializationServices.RegisterReply> getRegisterClientMethod;
    if ((getRegisterClientMethod = InitializationGrpc.getRegisterClientMethod) == null) {
      synchronized (InitializationGrpc.class) {
        if ((getRegisterClientMethod = InitializationGrpc.getRegisterClientMethod) == null) {
          InitializationGrpc.getRegisterClientMethod = getRegisterClientMethod =
              io.grpc.MethodDescriptor.<InitializationServices.RegisterRequest, InitializationServices.RegisterReply>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "RegisterClient"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  InitializationServices.RegisterRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  InitializationServices.RegisterReply.getDefaultInstance()))
              .setSchemaDescriptor(new InitializationMethodDescriptorSupplier("RegisterClient"))
              .build();
        }
      }
    }
    return getRegisterClientMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static InitializationStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<InitializationStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<InitializationStub>() {
        @java.lang.Override
        public InitializationStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new InitializationStub(channel, callOptions);
        }
      };
    return InitializationStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static InitializationBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<InitializationBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<InitializationBlockingStub>() {
        @java.lang.Override
        public InitializationBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new InitializationBlockingStub(channel, callOptions);
        }
      };
    return InitializationBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static InitializationFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<InitializationFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<InitializationFutureStub>() {
        @java.lang.Override
        public InitializationFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new InitializationFutureStub(channel, callOptions);
        }
      };
    return InitializationFutureStub.newStub(factory, channel);
  }

  /**
   */
  public static abstract class InitializationImplBase implements io.grpc.BindableService {

    /**
     */
    public void registerClient(InitializationServices.RegisterRequest request,
        io.grpc.stub.StreamObserver<InitializationServices.RegisterReply> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getRegisterClientMethod(), responseObserver);
    }

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return io.grpc.ServerServiceDefinition.builder(getServiceDescriptor())
          .addMethod(
            getRegisterClientMethod(),
            io.grpc.stub.ServerCalls.asyncUnaryCall(
              new MethodHandlers<
                InitializationServices.RegisterRequest,
                InitializationServices.RegisterReply>(
                  this, METHODID_REGISTER_CLIENT)))
          .build();
    }
  }

  /**
   */
  public static final class InitializationStub extends io.grpc.stub.AbstractAsyncStub<InitializationStub> {
    private InitializationStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected InitializationStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new InitializationStub(channel, callOptions);
    }

    /**
     */
    public void registerClient(InitializationServices.RegisterRequest request,
        io.grpc.stub.StreamObserver<InitializationServices.RegisterReply> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getRegisterClientMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   */
  public static final class InitializationBlockingStub extends io.grpc.stub.AbstractBlockingStub<InitializationBlockingStub> {
    private InitializationBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected InitializationBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new InitializationBlockingStub(channel, callOptions);
    }

    /**
     */
    public InitializationServices.RegisterReply registerClient(InitializationServices.RegisterRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getRegisterClientMethod(), getCallOptions(), request);
    }
  }

  /**
   */
  public static final class InitializationFutureStub extends io.grpc.stub.AbstractFutureStub<InitializationFutureStub> {
    private InitializationFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected InitializationFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new InitializationFutureStub(channel, callOptions);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<InitializationServices.RegisterReply> registerClient(
        InitializationServices.RegisterRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getRegisterClientMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_REGISTER_CLIENT = 0;

  private static final class MethodHandlers<Req, Resp> implements
      io.grpc.stub.ServerCalls.UnaryMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ServerStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ClientStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.BidiStreamingMethod<Req, Resp> {
    private final InitializationImplBase serviceImpl;
    private final int methodId;

    MethodHandlers(InitializationImplBase serviceImpl, int methodId) {
      this.serviceImpl = serviceImpl;
      this.methodId = methodId;
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public void invoke(Req request, io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        case METHODID_REGISTER_CLIENT:
          serviceImpl.registerClient((InitializationServices.RegisterRequest) request,
              (io.grpc.stub.StreamObserver<InitializationServices.RegisterReply>) responseObserver);
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

  private static abstract class InitializationBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    InitializationBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return InitializationServices.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("Initialization");
    }
  }

  private static final class InitializationFileDescriptorSupplier
      extends InitializationBaseDescriptorSupplier {
    InitializationFileDescriptorSupplier() {}
  }

  private static final class InitializationMethodDescriptorSupplier
      extends InitializationBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final String methodName;

    InitializationMethodDescriptorSupplier(String methodName) {
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
      synchronized (InitializationGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new InitializationFileDescriptorSupplier())
              .addMethod(getRegisterClientMethod())
              .build();
        }
      }
    }
    return result;
  }
}
