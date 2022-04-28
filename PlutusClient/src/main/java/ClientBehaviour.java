public class ClientBehaviour implements Runnable{

    //TODO: APIs to connect to the backends


    @Override
    public void run () {
        System.out.println("Hi, welcome to PlutusDB");
        System.out.println("Press a key to end this demo and prove that the user interaction is working.");
        String message = System.console().readLine();
        System.out.println("You inserted " + message +  " ... AU REVOIR!");
        System.exit(0);

    }
}
