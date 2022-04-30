import com.amazonaws.client.builder.AwsClientBuilder;
import com.amazonaws.services.dynamodbv2.AmazonDynamoDB;
import com.amazonaws.services.dynamodbv2.AmazonDynamoDBClientBuilder;
import com.amazonaws.services.dynamodbv2.document.DynamoDB;
import com.datastax.oss.driver.api.core.session.Session;

public class DatabaseController {

    private static DynamoDB dynamoDB;
//    private Cluster cluster;
    private Session session;

    public DatabaseController () {
        AmazonDynamoDB client = AmazonDynamoDBClientBuilder.standard()
                .withEndpointConfiguration(new AwsClientBuilder.EndpointConfiguration("http://localhost:8000", "us-west-2"))
                .build();

        dynamoDB = new DynamoDB(client);
    }

//    public void connectToCassandra(String node, Integer port) {
//        Cluster c;
//        Cluster.Builder b = Cluster.builder().addContactPoint(node);
//        if (port != null) {
//            b.withPort(port);
//        }
//        cluster = b.build();
//
//        session = cluster.connect();
//    }
//
//    public Session getSession() {
//        return this.session;
//    }
//
//    public void close() {
//        session.close();
//        cluster.close();
//    }

    public byte[] readDynamo(String id){
        return null;
    }

    public void writeDynamo(String id, byte[] newValue){
    }

    public boolean deleteDynamo(String id){
        return false;
    }

    public byte[] readCassandra (String key){
        return null;
    }

    public void writeCassandra(String id, byte[] newValue){
    }

    public boolean deleteCassandra(String id){
        return false;
    }
}
