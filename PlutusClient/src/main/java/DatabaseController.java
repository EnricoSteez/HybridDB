import com.amazonaws.client.builder.AwsClientBuilder;
import com.amazonaws.services.dynamodbv2.AmazonDynamoDB;
import com.amazonaws.services.dynamodbv2.AmazonDynamoDBClientBuilder;
import com.amazonaws.services.dynamodbv2.document.DynamoDB;
import com.amazonaws.services.dynamodbv2.document.Item;
import com.amazonaws.services.dynamodbv2.document.Table;
import com.amazonaws.services.dynamodbv2.document.spec.GetItemSpec;
import com.datastax.oss.driver.api.core.CqlSession;
import com.datastax.oss.driver.api.core.cql.ResultSet;
import com.datastax.oss.driver.api.core.cql.Row;
import com.datastax.oss.driver.api.core.cql.SimpleStatement;

import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;

public class DatabaseController {

    private static DynamoDB dynamoDB;
    //    private Cluster cluster;
    private static CqlSession cqlSession;

    public DatabaseController () {
        AmazonDynamoDB client = AmazonDynamoDBClientBuilder.standard()
                .withEndpointConfiguration(new AwsClientBuilder.EndpointConfiguration("http://localhost:8000", "us-west-2"))
                .build();

        dynamoDB = new DynamoDB(client);
        cqlSession = CqlSession.builder()
                .addContactPoint(new InetSocketAddress("127.0.0.1", 9042))
                .withKeyspace("demo")
                .withLocalDatacenter("datacenter1").build();
    }

    public byte[] readDynamo (String key) { // GET
        Table table = dynamoDB.getTable("items");
        GetItemSpec getItemSpec = new GetItemSpec()
                .withPrimaryKey("key", key);
        Item item = table.getItem(getItemSpec);

        return item.getJSON("value").substring(1).getBytes(StandardCharsets.UTF_8);
    }

    public void writeDynamo (String key, byte[] newValue) { //PUT / UPDATE
        Item item = new Item()
                .withPrimaryKey("key",key)
                .withString("value", new String(newValue));
        Table table = dynamoDB.getTable("items");
        table.putItem(item);
    }

    public void deleteDynamo (String key) { //DELETE
        Table table = dynamoDB.getTable("items");
        table.deleteItem("key", key);
    }

    public byte[] readCassandra (String key) {
        SimpleStatement stmt =
                SimpleStatement.builder("select * from items where key=?")
                .addPositionalValue(key)
                .build();
        ResultSet rs = cqlSession.execute(stmt);
        Row row = rs.one();
        System.out.println(row.getFormattedContents());
        return null;
    }

    public void writeCassandra (String key, byte[] newValue) {
        SimpleStatement stmt =
                SimpleStatement.builder("update items set value=? where key=?")
                        .addPositionalValues(key,newValue)
                        .build();
        cqlSession.execute(stmt);
    }

    public void deleteCassandra (String key) {
        SimpleStatement stmt =
                SimpleStatement.builder("delete from items where key=?")
                        .addPositionalValue(key)
                        .build();
        cqlSession.execute(stmt);
    }
}

