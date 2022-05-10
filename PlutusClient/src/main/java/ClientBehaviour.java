import java.util.HashMap;
import java.util.HashSet;
import java.util.StringTokenizer;

public class ClientBehaviour implements Runnable {

    //TODO: APIs to connect to the backends
    private final DatabaseController controller;
    private final HashSet<String> dynamoItems;

    public ClientBehaviour () {
        controller= new DatabaseController();
        dynamoItems = new HashSet<>();
    }

    @Override
    public void run () {
        System.out.println("Hi, welcome to PlutusDB");
        System.out.println(
                "Command list:\n" +
                        "- write <key> <value>" +
                        "- read <key>" +
                        "- delete <key>" +
                        "- exit"
        );
        String message = System.console().readLine();
        while (!message.equals("exit")) {
            StringTokenizer tokenizer = new StringTokenizer(message);
            int n = tokenizer.countTokens();
            String op = tokenizer.nextToken();
            switch (op) {
                case "write":
                    if (n != 3) {
                        System.out.println("Wrong command syntax");
                        break;
                    }
                    
                    String key = tokenizer.nextToken();
                    String value = tokenizer.nextToken();

                    break;
                case "read":
                    break;
                case "delete":
                    break;
                default:
                    break;
            }

            message = System.console().readLine();

        }

        System.out.println("\n... AU REVOIR!");
        System.exit(0);

    }
}
